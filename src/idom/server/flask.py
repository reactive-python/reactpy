from __future__ import annotations

import asyncio
import json
import logging
from asyncio import Queue as AsyncQueue
from queue import Queue as ThreadQueue
from threading import Event as ThreadEvent
from threading import Thread
from typing import Any, Callable, Dict, NamedTuple, Optional, Union, cast
from urllib.parse import parse_qs as parse_query_string

from flask import Blueprint, Flask, redirect, request, send_from_directory, url_for
from flask_cors import CORS
from flask_sockets import Sockets
from geventwebsocket.websocket import WebSocket
from typing_extensions import TypedDict
from werkzeug.serving import ThreadedWSGIServer

import idom
from idom.config import IDOM_DEBUG_MODE, IDOM_WEB_MODULES_DIR
from idom.core.dispatcher import dispatch_single_view
from idom.core.layout import LayoutEvent, LayoutUpdate
from idom.core.types import ComponentConstructor, ComponentType

from .utils import CLIENT_BUILD_DIR


logger = logging.getLogger(__name__)


def configure(
    app: Flask, component: ComponentConstructor, options: Options | None = None
) -> None:
    """Return a :class:`FlaskServer` where each client has its own state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        constructor: A component constructor
        options: Options for configuring server behavior
        app: An application instance (otherwise a default instance is created)
    """
    options = _setup_options(options)
    blueprint = Blueprint("idom", __name__, url_prefix=options["url_prefix"])
    _setup_common_routes(blueprint, options)
    _setup_single_view_dispatcher_route(app, options, component)
    app.register_blueprint(blueprint)


def create_development_app() -> Flask:
    """Create an application instance for development purposes"""
    return Flask(__name__)


async def serve_development_app(
    app: Flask, host: str, port: int, started: asyncio.Event
) -> None:
    """Run an application using a development server"""
    loop = asyncio.get_event_loop()

    @app.before_first_request
    def set_started():
        loop.call_soon_threadsafe(started.set)

    server = ThreadedWSGIServer(host, port, app)

    stopped = asyncio.Event()

    def run_server():
        try:
            server.serve_forever()
        finally:
            loop.call_soon_threadsafe(stopped.set)

    thread = Thread(target=run_server, daemon=True)

    try:
        await stopped.wait()
    finally:
        # we may have exitted because this task was cancelled
        server.shutdown()
        # the thread should eventually join
        thread.join(timeout=3)
        # just double check it happened
        if thread.is_alive():
            raise RuntimeError("Failed to shutdown server.")


class Options(TypedDict, total=False):
    """Render server config for :class:`FlaskRenderServer`"""

    cors: Union[bool, Dict[str, Any]]
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``flask_cors.CORS``
    """

    import_name: str
    """The module where the application instance was created

    For more info see :class:`flask.Flask`.
    """

    redirect_root_to_index: bool
    """Whether to redirect the root URL (with prefix) to ``index.html``"""

    serve_static_files: bool
    """Whether or not to serve static files (i.e. web modules)"""

    url_prefix: str
    """The URL prefix where IDOM resources will be served from"""


def _setup_options(options: Options | None) -> Options:
    return {
        "url_prefix": "",
        "cors": False,
        "serve_static_files": True,
        "redirect_root_to_index": True,
        **(options or {}),  # type: ignore
    }


def _setup_common_routes(blueprint: Blueprint, options: Options) -> None:
    cors_options = options["cors"]
    if cors_options:  # pragma: no cover
        cors_params = cors_options if isinstance(cors_options, dict) else {}
        CORS(blueprint, **cors_params)

    if options["serve_static_files"]:

        @blueprint.route("/client/<path:path>")
        def send_client_dir(path: str) -> Any:
            return send_from_directory(str(CLIENT_BUILD_DIR), path)

        @blueprint.route("/modules/<path:path>")
        def send_modules_dir(path: str) -> Any:
            return send_from_directory(str(IDOM_WEB_MODULES_DIR.current), path)

        if options["redirect_root_to_index"]:

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
    app: Flask, options: Options, constructor: ComponentConstructor
) -> None:
    sockets = Sockets(app)

    @sockets.route(_join_url_paths(options["url_prefix"], "/stream"))  # type: ignore
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


def _join_url_paths(*args: str) -> str:
    # urllib.parse.urljoin performs more logic than is needed. Thus we need a util func
    # to join paths as if they were POSIX paths.
    return "/".join(map(lambda x: str(x).rstrip("/"), filter(None, args)))
