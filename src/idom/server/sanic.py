"""
Sanic Servers
=============
"""
from __future__ import annotations

import asyncio
import json
import logging
from asyncio import Future
from asyncio.events import AbstractEventLoop
from threading import Event
from typing import Any, Dict, Optional, Tuple, Union

from mypy_extensions import TypedDict
from sanic import Blueprint, Sanic, request, response
from sanic_cors import CORS
from websockets import WebSocketCommonProtocol

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

from .utils import CLIENT_BUILD_DIR, threaded, wait_on_event


logger = logging.getLogger(__name__)

_SERVER_COUNT = 0


class Config(TypedDict, total=False):
    """Config for :class:`SanicRenderServer`"""

    cors: Union[bool, Dict[str, Any]]
    url_prefix: str
    serve_static_files: bool
    redirect_root_to_index: bool


def PerClientStateServer(
    constructor: ComponentConstructor,
    config: Optional[Config] = None,
    app: Optional[Sanic] = None,
) -> SanicServer:
    """Return a :class:`SanicServer` where each client has its own state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        constructor: A component constructor
        config: Options for configuring server behavior
        app: An application instance (otherwise a default instance is created)
    """
    config, app = _setup_config_and_app(config, app)
    blueprint = Blueprint(f"idom_dispatcher_{id(app)}", url_prefix=config["url_prefix"])
    _setup_common_routes(blueprint, config)
    _setup_single_view_dispatcher_route(blueprint, constructor)
    app.blueprint(blueprint)
    return SanicServer(app)


def SharedClientStateServer(
    constructor: ComponentConstructor,
    config: Optional[Config] = None,
    app: Optional[Sanic] = None,
) -> SanicServer:
    """Return a :class:`SanicServer` where each client shares state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        constructor: A component constructor
        config: Options for configuring server behavior
        app: An application instance (otherwise a default instance is created)
    """
    config, app = _setup_config_and_app(config, app)
    blueprint = Blueprint(f"idom_dispatcher_{id(app)}", url_prefix=config["url_prefix"])
    _setup_common_routes(blueprint, config)
    _setup_shared_view_dispatcher_route(app, blueprint, constructor)
    app.blueprint(blueprint)
    return SanicServer(app)


class SanicServer:
    """A thin wrapper for running a Sanic application

    See :class:`idom.server.proto.Server` for more info
    """

    _loop: AbstractEventLoop

    def __init__(self, app: Sanic) -> None:
        self.app = app
        self._did_start = Event()
        self._did_stop = Event()
        app.register_listener(self._server_did_start, "after_server_start")
        app.register_listener(self._server_did_stop, "after_server_stop")

    def run(self, host: str, port: int, *args: Any, **kwargs: Any) -> None:
        self.app.run(host, port, *args, **kwargs)  # pragma: no cover

    @threaded
    def run_in_thread(self, host: str, port: int, *args: Any, **kwargs: Any) -> None:
        loop = asyncio.get_event_loop()

        # what follows was copied from:
        # https://github.com/sanic-org/sanic/blob/7028eae083b0da72d09111b9892ddcc00bce7df4/examples/run_async_advanced.py

        serv_coro = self.app.create_server(
            host, port, *args, **kwargs, return_asyncio_server=True
        )
        serv_task = asyncio.ensure_future(serv_coro, loop=loop)
        server = loop.run_until_complete(serv_task)
        server.after_start()
        try:
            loop.run_forever()
        except KeyboardInterrupt:  # pragma: no cover
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

    def wait_until_started(self, timeout: Optional[float] = 3.0) -> None:
        wait_on_event(f"start {self.app}", self._did_start, timeout)

    def stop(self, timeout: Optional[float] = 3.0) -> None:
        self._loop.call_soon_threadsafe(self.app.stop)
        wait_on_event(f"stop {self.app}", self._did_stop, timeout)

    async def _server_did_start(self, app: Sanic, loop: AbstractEventLoop) -> None:
        self._loop = loop
        self._did_start.set()

    async def _server_did_stop(self, app: Sanic, loop: AbstractEventLoop) -> None:
        self._did_stop.set()


def _setup_config_and_app(
    config: Optional[Config],
    app: Optional[Sanic],
) -> Tuple[Config, Sanic]:
    if app is None:
        global _SERVER_COUNT
        _SERVER_COUNT += 1
        app = Sanic(f"{__name__}[{_SERVER_COUNT}]")
    return (
        {
            "cors": False,
            "url_prefix": "",
            "serve_static_files": True,
            "redirect_root_to_index": True,
            **(config or {}),  # type: ignore
        },
        app,
    )


def _setup_common_routes(blueprint: Blueprint, config: Config) -> None:
    cors_config = config["cors"]
    if cors_config:  # pragma: no cover
        cors_params = cors_config if isinstance(cors_config, dict) else {}
        CORS(blueprint, **cors_params)

    if config["serve_static_files"]:
        blueprint.static("/client", str(CLIENT_BUILD_DIR))
        blueprint.static("/modules", str(IDOM_WED_MODULES_DIR.current))

        if config["redirect_root_to_index"]:

            @blueprint.route("/")  # type: ignore
            def redirect_to_index(
                request: request.Request,
            ) -> response.HTTPResponse:
                return response.redirect(
                    f"{blueprint.url_prefix}/client/index.html?{request.query_string}"
                )


def _setup_single_view_dispatcher_route(
    blueprint: Blueprint, constructor: ComponentConstructor
) -> None:
    @blueprint.websocket("/stream")  # type: ignore
    async def model_stream(
        request: request.Request, socket: WebSocketCommonProtocol
    ) -> None:
        send, recv = _make_send_recv_callbacks(socket)
        component_params = {k: request.args.get(k) for k in request.args}
        await dispatch_single_view(Layout(constructor(**component_params)), send, recv)


def _setup_shared_view_dispatcher_route(
    app: Sanic, blueprint: Blueprint, constructor: ComponentConstructor
) -> None:
    dispatcher_future: Future[None]
    dispatch_coroutine: SharedViewDispatcher

    async def activate_dispatcher(app: Sanic, loop: AbstractEventLoop) -> None:
        nonlocal dispatcher_future
        nonlocal dispatch_coroutine
        dispatcher_future, dispatch_coroutine = ensure_shared_view_dispatcher_future(
            Layout(constructor())
        )

    async def deactivate_dispatcher(app: Sanic, loop: AbstractEventLoop) -> None:
        logger.debug("Stopping dispatcher - server is shutting down")
        dispatcher_future.cancel()
        await asyncio.wait([dispatcher_future])

    app.register_listener(activate_dispatcher, "before_server_start")
    app.register_listener(deactivate_dispatcher, "before_server_stop")

    @blueprint.websocket("/stream")  # type: ignore
    async def model_stream(
        request: request.Request, socket: WebSocketCommonProtocol
    ) -> None:
        if request.args:
            raise ValueError(
                "SharedClientState server does not support per-client view parameters"
            )
        send, recv = _make_send_recv_callbacks(socket)
        await dispatch_coroutine(send, recv)


def _make_send_recv_callbacks(
    socket: WebSocketCommonProtocol,
) -> Tuple[SendCoroutine, RecvCoroutine]:
    async def sock_send(value: LayoutUpdate) -> None:
        await socket.send(json.dumps(value))

    async def sock_recv() -> LayoutEvent:
        return LayoutEvent(**json.loads(await socket.recv()))

    return sock_send, sock_recv
