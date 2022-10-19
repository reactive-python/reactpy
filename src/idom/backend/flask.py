from __future__ import annotations

import asyncio
import json
import logging
import os
from asyncio import Queue as AsyncQueue
from dataclasses import dataclass
from queue import Queue as ThreadQueue
from threading import Event as ThreadEvent
from threading import Thread
from typing import Any, Callable, Dict, NamedTuple, NoReturn, Optional, Union, cast

from flask import (
    Blueprint,
    Flask,
    Request,
    copy_current_request_context,
    request,
    send_file,
)
from flask_cors import CORS
from flask_sock import Sock
from simple_websocket import Server as WebSocket
from werkzeug.local import LocalProxy
from werkzeug.serving import BaseWSGIServer, make_server

import idom
from idom.backend.hooks import ConnectionContext
from idom.backend.hooks import use_connection as _use_connection
from idom.backend.types import Connection, Location
from idom.core.layout import LayoutEvent, LayoutUpdate
from idom.core.serve import serve_json_patch
from idom.core.types import ComponentType, RootComponentConstructor
from idom.utils import Ref

from .utils import safe_client_build_dir_path, safe_web_modules_dir_path


logger = logging.getLogger(__name__)


def configure(
    app: Flask, component: RootComponentConstructor, options: Options | None = None
) -> None:
    """Configure the necessary IDOM routes on the given app.

    Parameters:
        app: An application instance
        component: A component constructor
        options: Options for configuring server behavior
    """
    options = options or Options()
    blueprint = Blueprint("idom", __name__, url_prefix=options.url_prefix)

    # this route should take priority so set up it up first
    _setup_single_view_dispatcher_route(blueprint, options, component)

    _setup_common_routes(blueprint, options)

    app.register_blueprint(blueprint)


def create_development_app() -> Flask:
    """Create an application instance for development purposes"""
    os.environ["FLASK_DEBUG"] = "true"
    app = Flask(__name__)
    return app


async def serve_development_app(
    app: Flask,
    host: str,
    port: int,
    started: asyncio.Event | None = None,
) -> None:
    """Run an application using a development server"""
    loop = asyncio.get_event_loop()
    stopped = asyncio.Event()

    server: Ref[BaseWSGIServer] = Ref()

    def run_server() -> None:
        server.current = make_server(host, port, app, threaded=True)
        if started:
            loop.call_soon_threadsafe(started.set)
        try:
            server.current.serve_forever()  # type: ignore
        finally:
            loop.call_soon_threadsafe(stopped.set)

    thread = Thread(target=run_server, daemon=True)
    thread.start()

    if started:
        await started.wait()

    try:
        await stopped.wait()
    finally:
        # we may have exitted because this task was cancelled
        server.current.shutdown()
        # the thread should eventually join
        thread.join(timeout=3)
        # just double check it happened
        if thread.is_alive():  # pragma: no cover
            raise RuntimeError("Failed to shutdown server.")


def use_websocket() -> WebSocket:
    """A handle to the current websocket"""
    return use_connection().carrier.websocket


def use_request() -> Request:
    """Get the current ``Request``"""
    return use_connection().carrier.request


def use_connection() -> Connection[_FlaskCarrier]:
    """Get the current :class:`Connection`"""
    conn = _use_connection()
    if not isinstance(conn.carrier, _FlaskCarrier):
        raise TypeError(  # pragma: no cover
            f"Connection has unexpected carrier {conn.carrier}. "
            "Are you running with a Flask server?"
        )
    return conn


@dataclass
class Options:
    """Render server config for :class:`FlaskRenderServer`"""

    cors: Union[bool, Dict[str, Any]] = False
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``flask_cors.CORS``
    """

    serve_static_files: bool = True
    """Whether or not to serve static files (i.e. web modules)"""

    url_prefix: str = ""
    """The URL prefix where IDOM resources will be served from"""


def _setup_common_routes(blueprint: Blueprint, options: Options) -> None:
    cors_options = options.cors
    if cors_options:  # pragma: no cover
        cors_params = cors_options if isinstance(cors_options, dict) else {}
        CORS(blueprint, **cors_params)

    if options.serve_static_files:

        @blueprint.route("/")
        @blueprint.route("/<path:path>")
        def send_client_dir(path: str = "") -> Any:
            return send_file(safe_client_build_dir_path(path))

        @blueprint.route(r"/_api/modules/<path:path>")
        @blueprint.route(r"<path:_>/_api/modules/<path:path>")
        def send_modules_dir(
            path: str,
            _: str = "",  # this is not used
        ) -> Any:
            return send_file(safe_web_modules_dir_path(path))


def _setup_single_view_dispatcher_route(
    blueprint: Blueprint, options: Options, constructor: RootComponentConstructor
) -> None:
    sock = Sock(blueprint)

    def model_stream(ws: WebSocket, path: str = "") -> None:
        def send(value: Any) -> None:
            ws.send(json.dumps(value))

        def recv() -> LayoutEvent:
            return LayoutEvent(**json.loads(ws.receive()))

        _dispatch_in_thread(ws, path, constructor(), send, recv)

    sock.route("/_api/stream", endpoint="without_path")(model_stream)
    sock.route("/<path:path>/_api/stream", endpoint="with_path")(model_stream)


def _dispatch_in_thread(
    websocket: WebSocket,
    path: str,
    component: ComponentType,
    send: Callable[[Any], None],
    recv: Callable[[], Optional[LayoutEvent]],
) -> NoReturn:
    dispatch_thread_info_created = ThreadEvent()
    dispatch_thread_info_ref: idom.Ref[Optional[_DispatcherThreadInfo]] = idom.Ref(None)

    @copy_current_request_context
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
            search = request.query_string.decode()
            await serve_json_patch(
                idom.Layout(
                    ConnectionContext(
                        component,
                        value=Connection(
                            scope=request.environ,
                            location=Location(
                                pathname=f"/{path}",
                                search=f"?{search}" if search else "",
                            ),
                            carrier=_FlaskCarrier(request, websocket),
                        ),
                    ),
                ),
                send_coro,
                recv_coro,
            )

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
            dispatch_thread_info.dispatch_loop.call_soon_threadsafe(
                dispatch_thread_info.async_recv_queue.put_nowait, value
            )
    finally:  # pragma: no cover
        dispatch_thread_info.dispatch_loop.call_soon_threadsafe(
            dispatch_thread_info.dispatch_future.cancel
        )


class _DispatcherThreadInfo(NamedTuple):
    dispatch_loop: asyncio.AbstractEventLoop
    dispatch_future: "asyncio.Future[Any]"
    thread_send_queue: "ThreadQueue[LayoutUpdate]"
    async_recv_queue: "AsyncQueue[LayoutEvent]"


@dataclass
class _FlaskCarrier:
    """A simple wrapper for holding a Flask request and WebSocket"""

    request: Request
    """The current request object"""

    websocket: WebSocket
    """A handle to the current websocket"""
