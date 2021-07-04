"""
Flask Servers
=============
"""
from __future__ import annotations

import asyncio
import json
import logging
from asyncio import Queue as AsyncQueue
from queue import Queue as ThreadQueue
from threading import Event as ThreadEvent
from threading import Thread
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple, Union, cast
from urllib.parse import parse_qs as parse_query_string

from flask import Blueprint, Flask, redirect, request, send_from_directory, url_for
from flask_cors import CORS
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.websocket import WebSocket
from typing_extensions import TypedDict

import idom
from idom.config import IDOM_DEBUG_MODE, IDOM_WED_MODULES_DIR
from idom.core.component import ComponentConstructor, ComponentType
from idom.core.dispatcher import dispatch_single_view
from idom.core.layout import LayoutEvent, LayoutUpdate

from .utils import CLIENT_BUILD_DIR, threaded, wait_on_event


logger = logging.getLogger(__name__)


class Config(TypedDict, total=False):
    """Render server config for :class:`FlaskRenderServer`"""

    import_name: str
    url_prefix: str
    cors: Union[bool, Dict[str, Any]]
    serve_static_files: bool
    redirect_root_to_index: bool


def PerClientStateServer(
    constructor: ComponentConstructor,
    config: Optional[Config] = None,
    app: Optional[Flask] = None,
) -> FlaskServer:
    """Return a :class:`FlaskServer` where each client has its own state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        constructor: A component constructor
        config: Options for configuring server behavior
        app: An application instance (otherwise a default instance is created)
    """
    config, app = _setup_config_and_app(config, app)
    blueprint = Blueprint("idom", __name__, url_prefix=config["url_prefix"])
    _setup_common_routes(blueprint, config)
    _setup_single_view_dispatcher_route(app, config, constructor)
    app.register_blueprint(blueprint)
    return FlaskServer(app)


class FlaskServer:
    """A thin wrapper for running a Flask application

    See :class:`idom.server.proto.Server` for more info
    """

    _wsgi_server: pywsgi.WSGIServer

    def __init__(self, app: Flask) -> None:
        self.app = app
        self._did_start = ThreadEvent()

        @app.before_first_request
        def server_did_start() -> None:
            self._did_start.set()

    def run(self, host: str, port: int, *args: Any, **kwargs: Any) -> None:
        if IDOM_DEBUG_MODE.current:
            logging.basicConfig(level=logging.DEBUG)  # pragma: no cover
        logger.info(f"Running at http://{host}:{port}")
        self._wsgi_server = _StartCallbackWSGIServer(
            self._did_start.set,
            (host, port),
            self.app,
            *args,
            handler_class=WebSocketHandler,
            **kwargs,
        )
        self._wsgi_server.serve_forever()

    run_in_thread = threaded(run)

    def wait_until_started(self, timeout: Optional[float] = 3.0) -> None:
        wait_on_event(f"start {self.app}", self._did_start, timeout)

    def stop(self, timeout: Optional[float] = 3.0) -> None:
        try:
            server = self._wsgi_server
        except AttributeError:  # pragma: no cover
            raise RuntimeError(
                f"Application is not running or was not started by {self}"
            )
        else:
            server.stop(timeout)


def _setup_config_and_app(
    config: Optional[Config], app: Optional[Flask]
) -> Tuple[Config, Flask]:
    return (
        {
            "url_prefix": "",
            "cors": False,
            "serve_static_files": True,
            "redirect_root_to_index": True,
            **(config or {}),  # type: ignore
        },
        app or Flask(__name__),
    )


def _setup_common_routes(blueprint: Blueprint, config: Config) -> None:
    cors_config = config["cors"]
    if cors_config:  # pragma: no cover
        cors_params = cors_config if isinstance(cors_config, dict) else {}
        CORS(blueprint, **cors_params)

    if config["serve_static_files"]:

        @blueprint.route("/client/<path:path>")
        def send_client_dir(path: str) -> Any:
            return send_from_directory(str(CLIENT_BUILD_DIR), path)

        @blueprint.route("/modules/<path:path>")
        def send_modules_dir(path: str) -> Any:
            return send_from_directory(str(IDOM_WED_MODULES_DIR.current), path)

        if config["redirect_root_to_index"]:

            @blueprint.route("/")
            def redirect_to_index() -> Any:
                return redirect(
                    url_for(
                        "idom.send_client_dir",
                        path="index.html",
                        **request.args,
                    )
                )


def _setup_single_view_dispatcher_route(
    app: Flask, config: Config, constructor: ComponentConstructor
) -> None:
    sockets = Sockets(app)

    @sockets.route(_join_url_paths(config["url_prefix"], "/stream"))  # type: ignore
    def model_stream(ws: WebSocket) -> None:
        def send(value: Any) -> None:
            ws.send(json.dumps(value))

        def recv() -> Optional[LayoutEvent]:
            event = ws.receive()
            if event is not None:
                return LayoutEvent(**json.loads(event))
            else:
                return None

        dispatch_single_view_in_thread(constructor(**_get_query_params(ws)), send, recv)


def _get_query_params(ws: WebSocket) -> Dict[str, Any]:
    return {
        k: v if len(v) > 1 else v[0]
        for k, v in parse_query_string(ws.environ["QUERY_STRING"]).items()
    }


def dispatch_single_view_in_thread(
    component: ComponentType,
    send: Callable[[Any], None],
    recv: Callable[[], Optional[LayoutEvent]],
) -> None:
    dispatch_thread_info_created = ThreadEvent()
    dispatch_thread_info_ref: idom.Ref[Optional[_DispatcherThreadInfo]] = idom.Ref(None)

    def run_dispatcher() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        thread_send_queue: "ThreadQueue[LayoutUpdate]" = ThreadQueue()
        async_recv_queue: "AsyncQueue[LayoutEvent]" = AsyncQueue()

        async def send_coro(value: Any) -> None:
            thread_send_queue.put(value)

        async def recv_coro() -> Any:
            return await async_recv_queue.get()

        async def main() -> None:
            await dispatch_single_view(idom.Layout(component), send_coro, recv_coro)

        main_future = asyncio.ensure_future(main())

        dispatch_thread_info_ref.current = _DispatcherThreadInfo(
            dispatch_loop=loop,
            dispatch_future=main_future,
            thread_send_queue=thread_send_queue,
            async_recv_queue=async_recv_queue,
        )
        dispatch_thread_info_created.set()

        loop.run_until_complete(main_future)

    Thread(target=run_dispatcher, daemon=True).start()

    dispatch_thread_info_created.wait()
    dispatch_thread_info = cast(_DispatcherThreadInfo, dispatch_thread_info_ref.current)
    assert dispatch_thread_info is not None

    stop = ThreadEvent()

    def run_send() -> None:
        while not stop.is_set():
            send(dispatch_thread_info.thread_send_queue.get())

    Thread(target=run_send, daemon=True).start()

    try:
        while True:
            value = recv()
            if value is None:
                stop.set()
                break
            # BUG: https://github.com/nedbat/coveragepy/issues/1012
            # Coverage isn't able to support concurrency coverage for both threading and gevent
            dispatch_thread_info.dispatch_loop.call_soon_threadsafe(  # pragma: no cover
                dispatch_thread_info.async_recv_queue.put_nowait, value
            )
    finally:
        dispatch_thread_info.dispatch_loop.call_soon_threadsafe(
            dispatch_thread_info.dispatch_future.cancel
        )

    return None


class _DispatcherThreadInfo(NamedTuple):
    dispatch_loop: asyncio.AbstractEventLoop
    dispatch_future: "asyncio.Future[Any]"
    thread_send_queue: "ThreadQueue[LayoutUpdate]"
    async_recv_queue: "AsyncQueue[LayoutEvent]"


class _StartCallbackWSGIServer(pywsgi.WSGIServer):  # type: ignore
    def __init__(
        self, before_first_request: Callable[[], None], *args: Any, **kwargs: Any
    ) -> None:
        self._before_first_request_callback = before_first_request
        super().__init__(*args, **kwargs)

    def update_environ(self) -> None:
        """
        Called before the first request is handled to fill in WSGI environment values.

        This includes getting the correct server name and port.
        """
        super().update_environ()
        # BUG: https://github.com/nedbat/coveragepy/issues/1012
        # Coverage isn't able to support concurrency coverage for both threading and gevent
        self._before_first_request_callback()  # pragma: no cover


def _join_url_paths(*args: str) -> str:
    # urllib.parse.urljoin performs more logic than is needed. Thus we need a util func
    # to join paths as if they were POSIX paths.
    return "/".join(map(lambda x: str(x).rstrip("/"), filter(None, args)))
