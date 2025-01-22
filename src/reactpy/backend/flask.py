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
from typing import Any, Callable, NamedTuple, NoReturn, cast

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
from werkzeug.serving import BaseWSGIServer, make_server

import reactpy
from reactpy.backend._common import (
    ASSETS_PATH,
    MODULES_PATH,
    PATH_PREFIX,
    STREAM_PATH,
    CommonOptions,
    read_client_index_html,
    safe_client_build_dir_path,
    safe_web_modules_dir_path,
)
from reactpy.backend.types import Connection, Location
from reactpy.core.hooks import ConnectionContext
from reactpy.core.hooks import use_connection as _use_connection
from reactpy.core.serve import serve_layout
from reactpy.core.types import ComponentType, RootComponentConstructor
from reactpy.utils import Ref

logger = logging.getLogger(__name__)


# BackendType.Options
@dataclass
class Options(CommonOptions):
    """Render server config for :func:`reactpy.backend.flask.configure`"""

    cors: bool | dict[str, Any] = False
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``flask_cors.CORS``
    """


# BackendType.configure
def configure(
    app: Flask, component: RootComponentConstructor, options: Options | None = None
) -> None:
    """Configure the necessary ReactPy routes on the given app.

    Parameters:
        app: An application instance
        component: A component constructor
        options: Options for configuring server behavior
    """
    options = options or Options()

    api_bp = Blueprint(f"reactpy_api_{id(app)}", __name__, url_prefix=str(PATH_PREFIX))
    spa_bp = Blueprint(
        f"reactpy_spa_{id(app)}", __name__, url_prefix=options.url_prefix
    )

    _setup_single_view_dispatcher_route(api_bp, options, component)
    _setup_common_routes(api_bp, spa_bp, options)

    app.register_blueprint(api_bp)
    app.register_blueprint(spa_bp)


# BackendType.create_development_app
def create_development_app() -> Flask:
    """Create an application instance for development purposes"""
    os.environ["FLASK_DEBUG"] = "true"
    return Flask(__name__)


# BackendType.serve_development_app
async def serve_development_app(
    app: Flask,
    host: str,
    port: int,
    started: asyncio.Event | None = None,
) -> None:
    """Run a development server for FastAPI"""
    loop = asyncio.get_running_loop()
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
        # we may have exited because this task was cancelled
        server.current.shutdown()
        # the thread should eventually join
        thread.join(timeout=3)
        # just double check it happened
        if thread.is_alive():  # nocov
            msg = "Failed to shutdown server."
            raise RuntimeError(msg)


def use_websocket() -> WebSocket:
    """A handle to the current websocket"""
    return use_connection().carrier.websocket


def use_request() -> Request:
    """Get the current ``Request``"""
    return use_connection().carrier.request


def use_connection() -> Connection[_FlaskCarrier]:
    """Get the current :class:`Connection`"""
    conn = _use_connection()
    if not isinstance(conn.carrier, _FlaskCarrier):  # nocov
        msg = f"Connection has unexpected carrier {conn.carrier}. Are you running with a Flask server?"
        raise TypeError(msg)
    return conn


def _setup_common_routes(
    api_blueprint: Blueprint,
    spa_blueprint: Blueprint,
    options: Options,
) -> None:
    cors_options = options.cors
    if cors_options:  # nocov
        cors_params = cors_options if isinstance(cors_options, dict) else {}
        CORS(api_blueprint, **cors_params)

    @api_blueprint.route(f"/{ASSETS_PATH.name}/<path:path>")
    def send_assets_dir(path: str = "") -> Any:
        return send_file(safe_client_build_dir_path(f"assets/{path}"))

    @api_blueprint.route(f"/{MODULES_PATH.name}/<path:path>")
    def send_modules_dir(path: str = "") -> Any:
        return send_file(safe_web_modules_dir_path(path), mimetype="text/javascript")

    index_html = read_client_index_html(options)

    if options.serve_index_route:

        @spa_blueprint.route("/")
        @spa_blueprint.route("/<path:_>")
        def send_client_dir(_: str = "") -> Any:
            return index_html


def _setup_single_view_dispatcher_route(
    api_blueprint: Blueprint, options: Options, constructor: RootComponentConstructor
) -> None:
    sock = Sock(api_blueprint)

    def model_stream(ws: WebSocket, path: str = "") -> None:
        def send(value: Any) -> None:
            ws.send(json.dumps(value))

        def recv() -> Any:
            return json.loads(ws.receive())

        _dispatch_in_thread(
            ws,
            # remove any url prefix from path
            path[len(options.url_prefix) :],
            constructor(),
            send,
            recv,
        )

    sock.route(STREAM_PATH.name, endpoint="without_path")(model_stream)
    sock.route(f"{STREAM_PATH.name}/<path:path>", endpoint="with_path")(model_stream)


def _dispatch_in_thread(
    websocket: WebSocket,
    path: str,
    component: ComponentType,
    send: Callable[[Any], None],
    recv: Callable[[], Any | None],
) -> NoReturn:
    dispatch_thread_info_created = ThreadEvent()
    dispatch_thread_info_ref: reactpy.Ref[_DispatcherThreadInfo | None] = reactpy.Ref(
        None
    )

    @copy_current_request_context
    def run_dispatcher() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        thread_send_queue: ThreadQueue[Any] = ThreadQueue()
        async_recv_queue: AsyncQueue[Any] = AsyncQueue()

        async def send_coro(value: Any) -> None:
            thread_send_queue.put(value)

        async def main() -> None:
            search = request.query_string.decode()
            await serve_layout(
                reactpy.Layout(
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
                async_recv_queue.get,
            )

        main_future = asyncio.ensure_future(main(), loop=loop)

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

    if dispatch_thread_info is None:
        raise RuntimeError("Failed to create dispatcher thread")  # nocov

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
    finally:  # nocov
        dispatch_thread_info.dispatch_loop.call_soon_threadsafe(
            dispatch_thread_info.dispatch_future.cancel
        )


class _DispatcherThreadInfo(NamedTuple):
    dispatch_loop: asyncio.AbstractEventLoop
    dispatch_future: asyncio.Future[Any]
    thread_send_queue: ThreadQueue[Any]
    async_recv_queue: AsyncQueue[Any]


@dataclass
class _FlaskCarrier:
    """A simple wrapper for holding a Flask request and WebSocket"""

    request: Request
    """The current request object"""

    websocket: WebSocket
    """A handle to the current websocket"""
