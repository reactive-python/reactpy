import asyncio
import json
import uuid

from typing import Tuple, Any, Dict, Union, cast

from sanic import Blueprint, Sanic, request, response
from sanic_cors import CORS
from mypy_extensions import TypedDict
from websockets import WebSocketCommonProtocol

from idom.core.dispatcher import (
    SingleViewDispatcher,
    SharedViewDispatcher,
    SendCoroutine,
    RecvCoroutine,
)
from idom.core.layout import LayoutEvent
from idom.client.manage import BUILD_DIR

from .base import AbstractRenderServer


class Config(TypedDict, total=False):
    cors: Union[bool, Dict[str, Any]]
    url_prefix: str
    server_static_files: bool
    redirect_root_to_index: bool


class SanicRenderServer(AbstractRenderServer[Sanic, Config]):
    """Base ``sanic`` extension."""

    def _stop(self) -> None:
        self.application.stop()

    def _init_config(self) -> Config:
        return Config(
            cors=False,
            url_prefix="",
            server_static_files=True,
            redirect_root_to_index=True,
        )

    def _update_config(self, old: Config, new: Config) -> Config:
        old.update(new)
        return old

    def _default_application(self, config: Config) -> Sanic:
        return Sanic()

    def _setup_application(self, app: Sanic, config: Config) -> None:
        cors_config = config["cors"]
        if cors_config:
            cors_params = cors_config if isinstance(cors_config, dict) else {}
            CORS(app, **cors_params)

        bp = Blueprint(f"idom_dispatcher_{id(self)}", url_prefix=config["url_prefix"])
        self._setup_blueprint_routes(bp, config)
        app.blueprint(bp)

    def _setup_blueprint_routes(self, blueprint: Blueprint, config: Config) -> None:
        """Add routes to the application blueprint"""

        @blueprint.websocket("/stream")  # type: ignore
        async def model_stream(
            request: request.Request, socket: WebSocketCommonProtocol
        ) -> None:
            async def sock_send(value: Any) -> None:
                await socket.send(json.dumps(value))

            async def sock_recv() -> LayoutEvent:
                message = json.loads(await socket.recv())
                event = message["body"]["event"]
                return LayoutEvent(event["target"], event["data"])

            element_params = {k: request.args.get(k) for k in request.args}
            await self._run_dispatcher(sock_send, sock_recv, element_params)

        if config["server_static_files"]:
            blueprint.static("/client", str(BUILD_DIR))

        if config["server_static_files"] and config["redirect_root_to_index"]:

            @blueprint.route("/")  # type: ignore
            def redirect_to_index(request: request.Request) -> response.HTTPResponse:
                return response.redirect(f"{blueprint.url_prefix}/client/index.html")

    def _run_application(
        self, app: Sanic, config: Config, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> None:
        if not self._daemonized:
            app.run(*args, **kwargs)
        else:
            # copied from:
            # https://github.com/huge-success/sanic/blob/master/examples/run_async_advanced.py
            serv_coro = app.create_server(*args, **kwargs, return_asyncio_server=True)
            loop = asyncio.get_event_loop()
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


class PerClientStateServer(SanicRenderServer):
    """Each client view will have its own state."""

    _dispatcher_type = SingleViewDispatcher


class SharedClientStateServer(SanicRenderServer):
    """All connected client views will have shared state."""

    _dispatcher_type = SharedViewDispatcher
    _dispatcher: SharedViewDispatcher

    def _setup_application(self, app: Sanic, config: Config) -> None:
        app.listener("before_server_start")(self._activate_dispatcher)
        app.listener("before_server_stop")(self._deactivate_dispatcher)
        super()._setup_application(app, config)

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
