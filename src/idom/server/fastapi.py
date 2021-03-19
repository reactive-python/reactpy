import json
import logging
import sys
import time
import uuid
from threading import Event, Thread
from typing import Any, Dict, Optional, Tuple, Type, Union, cast

from fastapi import APIRouter, FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from mypy_extensions import TypedDict
from starlette.websockets import WebSocketDisconnect
from uvicorn.config import Config as UvicornConfig
from uvicorn.server import Server as UvicornServer
from uvicorn.supervisors.multiprocess import Multiprocess
from uvicorn.supervisors.statreload import StatReload as ChangeReload

from idom.config import IDOM_CLIENT_BUILD_DIR
from idom.core.dispatcher import (
    AbstractDispatcher,
    RecvCoroutine,
    SendCoroutine,
    SharedViewDispatcher,
    SingleViewDispatcher,
)
from idom.core.layout import Layout, LayoutEvent, LayoutUpdate

from .base import AbstractRenderServer


logger = logging.getLogger(__name__)


class Config(TypedDict, total=False):
    """Config for :class:`FastApiRenderServer`"""

    cors: Union[bool, Dict[str, Any]]
    url_prefix: str
    serve_static_files: bool
    redirect_root_to_index: bool


class FastApiRenderServer(AbstractRenderServer[FastAPI, Config]):
    """Base ``sanic`` extension."""

    _dispatcher_type: Type[AbstractDispatcher]
    _server: UvicornServer

    def stop(self, timeout: float = 3) -> None:
        """Stop the running application"""
        self._server.should_exit
        if self._daemon_thread is not None:
            self._daemon_thread.join(timeout)

    def _create_config(self, config: Optional[Config]) -> Config:
        new_config: Config = {
            "cors": False,
            "url_prefix": "",
            "serve_static_files": True,
            "redirect_root_to_index": True,
            **(config or {}),  # type: ignore
        }
        return new_config

    def _default_application(self, config: Config) -> FastAPI:
        return FastAPI()

    def _setup_application(self, config: Config, app: FastAPI) -> None:
        router = APIRouter(prefix=config["url_prefix"])

        self._setup_api_router(config, router)
        self._setup_static_files(config, app)

        cors_config = config["cors"]
        if cors_config:  # pragma: no cover
            cors_params = (
                cors_config
                if isinstance(cors_config, dict)
                else {"allow_origins": ["*"]}
            )
            app.add_middleware(CORSMiddleware, **cors_params)

        app.include_router(router)

    def _setup_application_did_start_event(
        self, config: Config, app: FastAPI, event: Event
    ) -> None:
        def target() -> None:
            while not hasattr(self, "_server") or not self._server.started:
                time.sleep(1e-3)
            event.set()

        Thread(target=target, daemon=True).start()

    def _setup_api_router(self, config: Config, router: APIRouter) -> None:
        """Add routes to the application blueprint"""

        @router.websocket("/stream")
        async def model_stream(socket: WebSocket) -> None:
            await socket.accept()

            async def sock_send(value: LayoutUpdate) -> None:
                await socket.send_text(json.dumps(value))

            async def sock_recv() -> LayoutEvent:
                return LayoutEvent(**json.loads(await socket.receive_text()))

            try:
                await self._run_dispatcher(
                    sock_send, sock_recv, dict(socket.query_params)
                )
            except WebSocketDisconnect as error:
                logger.info(f"WebSocket disconnect: {error.code}")

    def _setup_static_files(self, config: Config, app: FastAPI) -> None:
        # This really should be added to the APIRouter, but there's a bug in FastAPI
        # BUG: https://github.com/tiangolo/fastapi/issues/1469
        url_prefix = config["url_prefix"]
        if config["serve_static_files"]:
            app.mount(
                f"{url_prefix}/client",
                StaticFiles(
                    directory=str(IDOM_CLIENT_BUILD_DIR.get()),
                    html=True,
                    check_dir=True,
                ),
                name="idom_static_files",
            )

            if config["redirect_root_to_index"]:

                @app.route(f"{url_prefix}/")
                def redirect_to_index(request: Request) -> RedirectResponse:
                    return RedirectResponse(
                        f"{url_prefix}/client/index.html?{request.query_params}"
                    )

    def _run_application(
        self,
        config: Config,
        app: FastAPI,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._server = UvicornServer(
            UvicornConfig(app, host=host, port=port, loop="asyncio", *args, **kwargs)
        )
        _run_uvicorn_server(self._server)

    def _run_application_in_thread(
        self,
        config: Config,
        app: FastAPI,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        # uvicorn does the event loop setup for us
        self._run_application(config, app, host, port, args, kwargs)

    async def _run_dispatcher(
        self,
        send: SendCoroutine,
        recv: RecvCoroutine,
        params: Dict[str, Any],
    ) -> None:
        async with self._make_dispatcher(params) as dispatcher:
            await dispatcher.run(send, recv, None)

    def _make_dispatcher(self, params: Dict[str, Any]) -> AbstractDispatcher:
        return self._dispatcher_type(Layout(self._root_component_constructor(**params)))


class PerClientStateServer(FastApiRenderServer):
    """Each client view will have its own state."""

    _dispatcher_type = SingleViewDispatcher


class SharedClientStateServer(FastApiRenderServer):
    """All connected client views will have shared state."""

    _dispatcher_type = SharedViewDispatcher
    _dispatcher: SharedViewDispatcher

    def _setup_application(self, config: Config, app: FastAPI) -> None:
        app.on_event("startup")(self._activate_dispatcher)
        app.on_event("shutdown")(self._deactivate_dispatcher)
        super()._setup_application(config, app)

    async def _activate_dispatcher(self) -> None:
        self._dispatcher = cast(SharedViewDispatcher, self._make_dispatcher({}))
        await self._dispatcher.start()

    async def _deactivate_dispatcher(self) -> None:  # pragma: no cover
        # this doesn't seem to get triggered during testing for some reason
        await self._dispatcher.stop()

    async def _run_dispatcher(
        self,
        send: SendCoroutine,
        recv: RecvCoroutine,
        params: Dict[str, Any],
    ) -> None:
        if params:
            msg = f"SharedClientState server does not support per-client view parameters {params}"
            raise ValueError(msg)
        await self._dispatcher.run(send, recv, uuid.uuid4().hex, join=True)


def _run_uvicorn_server(server: UvicornServer) -> None:
    # The following was copied from the uvicorn source with minimal modification. We
    # shouldn't need to do this, but unfortunately there's no easy way to gain access to
    # the server instance so you can stop it.
    # BUG: https://github.com/encode/uvicorn/issues/742
    config = server.config

    if (config.reload or config.workers > 1) and not isinstance(
        server.config.app, str
    ):  # pragma: no cover
        logger = logging.getLogger("uvicorn.error")
        logger.warning(
            "You must pass the application as an import string to enable 'reload' or "
            "'workers'."
        )
        sys.exit(1)

    if config.should_reload:  # pragma: no cover
        sock = config.bind_socket()
        supervisor = ChangeReload(config, target=server.run, sockets=[sock])
        supervisor.run()
    elif config.workers > 1:  # pragma: no cover
        sock = config.bind_socket()
        supervisor = Multiprocess(config, target=server.run, sockets=[sock])
        supervisor.run()
    else:
        import asyncio

        asyncio.set_event_loop(asyncio.new_event_loop())
        server.run()
