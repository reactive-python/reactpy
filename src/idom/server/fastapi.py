"""
FastAPI Servers
===============
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from asyncio import Future
from threading import Event, Thread, current_thread
from typing import Any, Dict, Optional, Tuple, Union

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

from idom.config import IDOM_WED_MODULES_DIR
from idom.core.component import ComponentConstructor
from idom.core.dispatcher import (
    RecvCoroutine,
    SendCoroutine,
    SharedViewDispatcher,
    dispatch_single_view,
    ensure_shared_view_dispatcher_future,
)
from idom.core.layout import Layout, LayoutEvent, LayoutUpdate

from .utils import CLIENT_BUILD_DIR, poll, threaded


logger = logging.getLogger(__name__)


class Config(TypedDict, total=False):
    """Config for :class:`FastApiRenderServer`"""

    cors: Union[bool, Dict[str, Any]]
    url_prefix: str
    serve_static_files: bool
    redirect_root_to_index: bool


def PerClientStateServer(
    constructor: ComponentConstructor,
    config: Optional[Config] = None,
    app: Optional[FastAPI] = None,
) -> FastApiServer:
    """Return a :class:`FastApiServer` where each client has its own state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        constructor: A component constructor
        config: Options for configuring server behavior
        app: An application instance (otherwise a default instance is created)
    """
    config, app = _setup_config_and_app(config, app)
    router = APIRouter(prefix=config["url_prefix"])
    _setup_common_routes(app, router, config)
    _setup_single_view_dispatcher_route(router, constructor)
    app.include_router(router)
    return FastApiServer(app)


def SharedClientStateServer(
    constructor: ComponentConstructor,
    config: Optional[Config] = None,
    app: Optional[FastAPI] = None,
) -> FastApiServer:
    """Return a :class:`FastApiServer` where each client shares state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        constructor: A component constructor
        config: Options for configuring server behavior
        app: An application instance (otherwise a default instance is created)
    """
    config, app = _setup_config_and_app(config, app)
    router = APIRouter(prefix=config["url_prefix"])
    _setup_common_routes(app, router, config)
    _setup_shared_view_dispatcher_route(app, router, constructor)
    app.include_router(router)
    return FastApiServer(app)


class FastApiServer:
    """A thin wrapper for running a FastAPI application

    See :class:`idom.server.proto.Server` for more info
    """

    _server: UvicornServer
    _current_thread: Thread

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self._did_stop = Event()
        app.on_event("shutdown")(self._server_did_stop)

    def run(self, host: str, port: int, *args: Any, **kwargs: Any) -> None:
        self._current_thread = current_thread()

        self._server = server = UvicornServer(
            UvicornConfig(
                self.app, host=host, port=port, loop="asyncio", *args, **kwargs
            )
        )

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

    run_in_thread = threaded(run)

    def wait_until_started(self, timeout: Optional[float] = 3.0) -> None:
        poll(
            f"start {self.app}",
            0.01,
            timeout,
            lambda: hasattr(self, "_server") and self._server.started,
        )

    def stop(self, timeout: Optional[float] = 3.0) -> None:
        self._server.should_exit = True
        self._did_stop.wait(timeout)

    async def _server_did_stop(self) -> None:
        self._did_stop.set()


def _setup_config_and_app(
    config: Optional[Config],
    app: Optional[FastAPI],
) -> Tuple[Config, FastAPI]:
    return (
        {
            "cors": False,
            "url_prefix": "",
            "serve_static_files": True,
            "redirect_root_to_index": True,
            **(config or {}),  # type: ignore
        },
        app or FastAPI(),
    )


def _setup_common_routes(app: FastAPI, router: APIRouter, config: Config) -> None:
    cors_config = config["cors"]
    if cors_config:  # pragma: no cover
        cors_params = (
            cors_config if isinstance(cors_config, dict) else {"allow_origins": ["*"]}
        )
        app.add_middleware(CORSMiddleware, **cors_params)

    # This really should be added to the APIRouter, but there's a bug in FastAPI
    # BUG: https://github.com/tiangolo/fastapi/issues/1469
    url_prefix = config["url_prefix"]
    if config["serve_static_files"]:
        app.mount(
            f"{url_prefix}/client",
            StaticFiles(
                directory=str(CLIENT_BUILD_DIR),
                html=True,
                check_dir=True,
            ),
            name="idom_static_files",
        )
        app.mount(
            f"{url_prefix}/modules",
            StaticFiles(
                directory=str(IDOM_WED_MODULES_DIR.current),
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


def _setup_single_view_dispatcher_route(
    router: APIRouter, constructor: ComponentConstructor
) -> None:
    @router.websocket("/stream")
    async def model_stream(socket: WebSocket) -> None:
        await socket.accept()
        send, recv = _make_send_recv_callbacks(socket)
        try:
            await dispatch_single_view(
                Layout(constructor(**dict(socket.query_params))), send, recv
            )
        except WebSocketDisconnect as error:
            logger.info(f"WebSocket disconnect: {error.code}")


def _setup_shared_view_dispatcher_route(
    app: FastAPI, router: APIRouter, constructor: ComponentConstructor
) -> None:
    dispatcher_future: Future[None]
    dispatch_coroutine: SharedViewDispatcher

    @app.on_event("startup")
    async def activate_dispatcher() -> None:
        nonlocal dispatcher_future
        nonlocal dispatch_coroutine
        dispatcher_future, dispatch_coroutine = ensure_shared_view_dispatcher_future(
            Layout(constructor())
        )

    @app.on_event("shutdown")
    async def deactivate_dispatcher() -> None:
        logger.debug("Stopping dispatcher - server is shutting down")
        dispatcher_future.cancel()
        await asyncio.wait([dispatcher_future])

    @router.websocket("/stream")
    async def model_stream(socket: WebSocket) -> None:
        await socket.accept()

        if socket.query_params:
            raise ValueError(
                "SharedClientState server does not support per-client view parameters"
            )

        send, recv = _make_send_recv_callbacks(socket)

        try:
            await dispatch_coroutine(send, recv)
        except WebSocketDisconnect as error:
            logger.info(f"WebSocket disconnect: {error.code}")


def _make_send_recv_callbacks(
    socket: WebSocket,
) -> Tuple[SendCoroutine, RecvCoroutine]:
    async def sock_send(value: LayoutUpdate) -> None:
        await socket.send_text(json.dumps(value))

    async def sock_recv() -> LayoutEvent:
        return LayoutEvent(**json.loads(await socket.receive_text()))

    return sock_send, sock_recv
