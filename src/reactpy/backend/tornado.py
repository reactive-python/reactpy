from __future__ import annotations

import asyncio
import json
from asyncio import Queue as AsyncQueue
from asyncio.futures import Future
from typing import Any
from urllib.parse import urljoin

from tornado.httpserver import HTTPServer
from tornado.httputil import HTTPServerRequest
from tornado.log import enable_pretty_logging
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler
from tornado.wsgi import WSGIContainer
from typing_extensions import TypeAlias

from reactpy.backend._common import (
    ASSETS_PATH,
    CLIENT_BUILD_DIR,
    MODULES_PATH,
    STREAM_PATH,
    CommonOptions,
    read_client_index_html,
)
from reactpy.backend.types import Connection, Location
from reactpy.config import REACTPY_WEB_MODULES_DIR
from reactpy.core.hooks import ConnectionContext
from reactpy.core.hooks import use_connection as _use_connection
from reactpy.core.layout import Layout
from reactpy.core.serve import serve_layout
from reactpy.core.types import ComponentConstructor

# BackendType.Options
Options = CommonOptions


# BackendType.configure
def configure(
    app: Application,
    component: ComponentConstructor,
    options: CommonOptions | None = None,
) -> None:
    """Configure the necessary ReactPy routes on the given app.

    Parameters:
        app: An application instance
        component: A component constructor
        options: Options for configuring server behavior
    """
    options = options or Options()
    _add_handler(
        app,
        options,
        (
            # this route should take priority so set up it up first
            _setup_single_view_dispatcher_route(component, options)
            + _setup_common_routes(options)
        ),
    )


# BackendType.create_development_app
def create_development_app() -> Application:
    return Application(debug=True)


# BackendType.serve_development_app
async def serve_development_app(
    app: Application,
    host: str,
    port: int,
    started: asyncio.Event | None = None,
) -> None:
    enable_pretty_logging()

    AsyncIOMainLoop.current().install()

    server = HTTPServer(app)
    server.listen(port, host)

    if started:
        # at this point the server is accepting connection
        started.set()

    try:
        # block forever - tornado has already set up its own background tasks
        await asyncio.get_running_loop().create_future()
    finally:
        # stop accepting new connections
        server.stop()
        # wait for existing connections to complete
        await server.close_all_connections()


def use_request() -> HTTPServerRequest:
    """Get the current ``HTTPServerRequest``"""
    return use_connection().carrier


def use_connection() -> Connection[HTTPServerRequest]:
    conn = _use_connection()
    if not isinstance(conn.carrier, HTTPServerRequest):  # nocov
        msg = f"Connection has unexpected carrier {conn.carrier}. Are you running with a Flask server?"
        raise TypeError(msg)
    return conn


_RouteHandlerSpecs: TypeAlias = "list[tuple[str, type[RequestHandler], Any]]"


def _setup_common_routes(options: Options) -> _RouteHandlerSpecs:
    return [
        (
            rf"{MODULES_PATH}/(.*)",
            StaticFileHandler,
            {"path": str(REACTPY_WEB_MODULES_DIR.current)},
        ),
        (
            rf"{ASSETS_PATH}/(.*)",
            StaticFileHandler,
            {"path": str(CLIENT_BUILD_DIR / "assets")},
        ),
    ] + (
        [
            (
                r"/(.*)",
                IndexHandler,
                {"index_html": read_client_index_html(options)},
            ),
        ]
        if options.serve_index_route
        else []
    )


def _add_handler(
    app: Application, options: Options, handlers: _RouteHandlerSpecs
) -> None:
    prefixed_handlers: list[Any] = [
        (urljoin(options.url_prefix, route_pattern), *tuple(handler_info))
        for route_pattern, *handler_info in handlers
    ]
    app.add_handlers(r".*", prefixed_handlers)


def _setup_single_view_dispatcher_route(
    constructor: ComponentConstructor, options: Options
) -> _RouteHandlerSpecs:
    return [
        (
            rf"{STREAM_PATH}/(.*)",
            ModelStreamHandler,
            {"component_constructor": constructor, "url_prefix": options.url_prefix},
        ),
        (
            str(STREAM_PATH),
            ModelStreamHandler,
            {"component_constructor": constructor, "url_prefix": options.url_prefix},
        ),
    ]


class IndexHandler(RequestHandler):
    _index_html: str

    def initialize(self, index_html: str) -> None:
        self._index_html = index_html

    async def get(self, _: str) -> None:
        self.finish(self._index_html)


class ModelStreamHandler(WebSocketHandler):
    """A web-socket handler that serves up a new model stream to each new client"""

    _dispatch_future: Future[None]
    _message_queue: AsyncQueue[str]

    def initialize(
        self, component_constructor: ComponentConstructor, url_prefix: str
    ) -> None:
        self._component_constructor = component_constructor
        self._url_prefix = url_prefix

    async def open(self, path: str = "", *args: Any, **kwargs: Any) -> None:
        message_queue: AsyncQueue[str] = AsyncQueue()

        async def send(value: Any) -> None:
            await self.write_message(json.dumps(value))

        async def recv() -> Any:
            return json.loads(await message_queue.get())

        self._message_queue = message_queue
        self._dispatch_future = asyncio.ensure_future(
            serve_layout(
                Layout(
                    ConnectionContext(
                        self._component_constructor(),
                        value=Connection(
                            scope=_FAKE_WSGI_CONTAINER.environ(self.request),
                            location=Location(
                                pathname=f"/{path[len(self._url_prefix):]}",
                                search=(
                                    f"?{self.request.query}"
                                    if self.request.query
                                    else ""
                                ),
                            ),
                            carrier=self.request,
                        ),
                    )
                ),
                send,
                recv,
            )
        )

    async def on_message(self, message: str | bytes) -> None:
        await self._message_queue.put(
            message if isinstance(message, str) else message.decode()
        )

    def on_close(self) -> None:
        if not self._dispatch_future.done():
            self._dispatch_future.cancel()


# The interface for WSGIContainer.environ changed in Tornado version 6.3 from
# a staticmethod to an instance method. Since we're not that concerned with
# the details of the WSGI app itself, we can just use a fake one.
# see: https://github.com/tornadoweb/tornado/pull/3231#issuecomment-1518957578
_FAKE_WSGI_CONTAINER = WSGIContainer(lambda *a, **kw: iter([]))
