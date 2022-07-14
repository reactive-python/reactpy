from __future__ import annotations

import asyncio
import json
from asyncio import Queue as AsyncQueue
from asyncio.futures import Future
from dataclasses import dataclass
from typing import Any, List, Tuple, Type, Union
from urllib.parse import urljoin

from tornado.httpserver import HTTPServer
from tornado.httputil import HTTPServerRequest
from tornado.log import enable_pretty_logging
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler
from tornado.wsgi import WSGIContainer

from idom.backend.types import Location
from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.hooks import Context, create_context, use_context
from idom.core.layout import Layout, LayoutEvent
from idom.core.serve import VdomJsonPatch, serve_json_patch
from idom.core.types import ComponentConstructor

from .utils import CLIENT_BUILD_DIR, safe_client_build_dir_path


ConnectionContext: Context[Connection | None] = create_context(None)


def configure(
    app: Application,
    component: ComponentConstructor,
    options: Options | None = None,
) -> None:
    """Configure the necessary IDOM routes on the given app.

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
            _setup_single_view_dispatcher_route(component)
            + _setup_common_routes(options)
        ),
    )


def create_development_app() -> Application:
    return Application(debug=True)


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
        await asyncio.get_event_loop().create_future()
    finally:
        # stop accepting new connections
        server.stop()
        # wait for existing connections to complete
        await server.close_all_connections()


def use_location() -> Location:
    """Get the current route as a string"""
    conn = use_connection()
    search = conn.request.query
    return Location(pathname="/" + conn.path, search="?" + search if search else "")


def use_scope() -> dict[str, Any]:
    """Get the current WSGI environment dictionary"""
    return WSGIContainer.environ(use_request())


def use_request() -> HTTPServerRequest:
    """Get the current ``HTTPServerRequest``"""
    return use_connection().request


def use_connection() -> Connection:
    connection = use_context(ConnectionContext)
    if connection is None:
        raise RuntimeError(  # pragma: no cover
            "No connection. Are you running with a Tornado server?"
        )
    return connection


@dataclass
class Connection:
    """A simple wrapper for holding connection information"""

    request: HTTPServerRequest
    """The current request object"""

    path: str
    """The current path being served"""


@dataclass
class Options:
    """Render server options for :class:`TornadoRenderServer` subclasses"""

    serve_static_files: bool = True
    """Whether or not to serve static files (i.e. web modules)"""

    url_prefix: str = ""
    """The URL prefix where IDOM resources will be served from"""


_RouteHandlerSpecs = List[Tuple[str, Type[RequestHandler], Any]]


def _setup_common_routes(options: Options) -> _RouteHandlerSpecs:
    handlers: _RouteHandlerSpecs = []

    if options.serve_static_files:
        handlers.append(
            (
                r"/.*/?_api/modules/(.*)",
                StaticFileHandler,
                {"path": str(IDOM_WEB_MODULES_DIR.current)},
            )
        )

        # register last to give lowest priority
        handlers.append(
            (
                r"/(.*)",
                SpaStaticFileHandler,
                {"path": str(CLIENT_BUILD_DIR)},
            )
        )

    return handlers


def _add_handler(
    app: Application, options: Options, handlers: _RouteHandlerSpecs
) -> None:
    prefixed_handlers: List[Any] = [
        (urljoin(options.url_prefix, route_pattern),) + tuple(handler_info)
        for route_pattern, *handler_info in handlers
    ]
    app.add_handlers(r".*", prefixed_handlers)


def _setup_single_view_dispatcher_route(
    constructor: ComponentConstructor,
) -> _RouteHandlerSpecs:
    return [
        (
            r"/(.*)/_api/stream",
            ModelStreamHandler,
            {"component_constructor": constructor},
        ),
        (
            r"/_api/stream",
            ModelStreamHandler,
            {"component_constructor": constructor},
        ),
    ]


class SpaStaticFileHandler(StaticFileHandler):
    async def get(self, path: str, include_body: bool = True) -> None:
        # Path safety is the responsibility of tornado.web.StaticFileHandler -
        # using `safe_client_build_dir_path` is for convenience in this case.
        return await super().get(safe_client_build_dir_path(path).name, include_body)


class ModelStreamHandler(WebSocketHandler):
    """A web-socket handler that serves up a new model stream to each new client"""

    _dispatch_future: Future[None]
    _message_queue: AsyncQueue[str]

    def initialize(self, component_constructor: ComponentConstructor) -> None:
        self._component_constructor = component_constructor

    async def open(self, path: str = "", *args: Any, **kwargs: Any) -> None:
        message_queue: "AsyncQueue[str]" = AsyncQueue()

        async def send(value: VdomJsonPatch) -> None:
            await self.write_message(json.dumps(value))

        async def recv() -> LayoutEvent:
            return LayoutEvent(**json.loads(await message_queue.get()))

        self._message_queue = message_queue
        self._dispatch_future = asyncio.ensure_future(
            serve_json_patch(
                Layout(
                    ConnectionContext(
                        self._component_constructor(),
                        value=Connection(self.request, path),
                    )
                ),
                send,
                recv,
            )
        )

    async def on_message(self, message: Union[str, bytes]) -> None:
        await self._message_queue.put(
            message if isinstance(message, str) else message.decode()
        )

    def on_close(self) -> None:
        if not self._dispatch_future.done():
            self._dispatch_future.cancel()
