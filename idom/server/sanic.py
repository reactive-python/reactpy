import asyncio
import json
import uuid
from threading import Event

from typing import Tuple, Any, Dict, Union, Optional, Type, cast

from sanic import Blueprint, Sanic, request, response
from sanic_cors import CORS
from mypy_extensions import TypedDict
from websockets import WebSocketCommonProtocol

from idom.core.dispatcher import (
    AbstractDispatcher,
    SingleViewDispatcher,
    SharedViewDispatcher,
    SendCoroutine,
    RecvCoroutine,
)
from idom.core.layout import LayoutEvent, Layout, LayoutUpdate
from idom.client.manage import BUILD_DIR

from .base import AbstractRenderServer


class Config(TypedDict, total=False):
    """Config for :class:`SanicRenderServer`"""

    cors: Union[bool, Dict[str, Any]]
    url_prefix: str
    server_static_files: bool
    redirect_root_to_index: bool


class SanicRenderServer(AbstractRenderServer[Sanic, Config]):
    """Base ``sanic`` extension."""

    _loop: asyncio.AbstractEventLoop
    _dispatcher_type: Type[AbstractDispatcher]

    def stop(self) -> None:
        """Stop the running application"""
        self._loop.call_soon_threadsafe(self.application.stop)

    def _create_config(self, config: Optional[Config]) -> Config:
        return Config(
            {
                "cors": False,
                "url_prefix": "",
                "serve_static_files": True,
                "redirect_root_to_index": True,
                **(config or {}),
            }
        )

    def _default_application(self, config: Config) -> Sanic:
        return Sanic()

    def _setup_application(self, config: Config, app: Sanic) -> None:
        bp = Blueprint(f"idom_dispatcher_{id(self)}", url_prefix=config["url_prefix"])

        self._setup_blueprint_routes(config, bp)

        cors_config = config["cors"]
        if cors_config:
            cors_params = cors_config if isinstance(cors_config, dict) else {}
            CORS(bp, **cors_params)

        app.blueprint(bp)

    def _setup_application_did_start_event(
        self, config: Config, app: Sanic, event: Event
    ) -> None:
        async def server_did_start(app: Sanic, loop: asyncio.AbstractEventLoop) -> None:
            event.set()

        app.register_listener(server_did_start, "after_server_start")

    def _setup_blueprint_routes(self, config: Config, blueprint: Blueprint) -> None:
        """Add routes to the application blueprint"""

        @blueprint.websocket("/stream")  # type: ignore
        async def model_stream(
            request: request.Request, socket: WebSocketCommonProtocol
        ) -> None:
            async def sock_send(value: LayoutUpdate) -> None:
                await socket.send(json.dumps(value))

            async def sock_recv() -> LayoutEvent:
                return LayoutEvent(**json.loads(await socket.recv()))

            component_params = {k: request.args.get(k) for k in request.args}
            await self._run_dispatcher(sock_send, sock_recv, component_params)

        if config["serve_static_files"]:
            blueprint.static("/client", str(BUILD_DIR))

            if config["redirect_root_to_index"]:

                @blueprint.route("/")  # type: ignore
                def redirect_to_index(
                    request: request.Request,
                ) -> response.HTTPResponse:
                    return response.redirect(
                        f"{blueprint.url_prefix}/client/index.html?{request.query_string}"
                    )

    def _run_application(
        self,
        config: Config,
        app: Sanic,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._loop = asyncio.get_event_loop()
        app.run(host, port, *args, **kwargs)

    def _run_application_in_thread(
        self,
        config: Config,
        app: Sanic,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        finally:
            self._loop = loop

        # what follows was copied from:
        # https://github.com/sanic-org/sanic/blob/7028eae083b0da72d09111b9892ddcc00bce7df4/examples/run_async_advanced.py

        serv_coro = app.create_server(
            host, port, *args, **kwargs, return_asyncio_server=True
        )
        serv_task = asyncio.ensure_future(serv_coro, loop=loop)
        server = loop.run_until_complete(serv_task)
        server.after_start()
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            loop.stop()
        finally:
            server.before_stop()

            # Wait for server to close
            close_task = server.close()
            loop.run_until_complete(close_task)

            # Complete all tasks on the loop
            for connection in server.connections:
                connection.close_if_idle()
            server.after_stop()

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


class PerClientStateServer(SanicRenderServer):
    """Each client view will have its own state."""

    _dispatcher_type = SingleViewDispatcher


class SharedClientStateServer(SanicRenderServer):
    """All connected client views will have shared state."""

    _dispatcher_type = SharedViewDispatcher
    _dispatcher: SharedViewDispatcher

    def _setup_application(self, config: Config, app: Sanic) -> None:
        app.register_listener(self._activate_dispatcher, "before_server_start")
        app.register_listener(self._deactivate_dispatcher, "before_server_stop")
        super()._setup_application(config, app)

    async def _activate_dispatcher(
        self, app: Sanic, loop: asyncio.AbstractEventLoop
    ) -> None:
        self._dispatcher = cast(SharedViewDispatcher, self._make_dispatcher({}))
        await self._dispatcher.start()

    async def _deactivate_dispatcher(
        self, app: Sanic, loop: asyncio.AbstractEventLoop
    ) -> None:  # pragma: no cover
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
