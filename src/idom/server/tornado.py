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
from tornado.web import Application, RedirectHandler, RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler
from tornado.wsgi import WSGIContainer

from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.hooks import Context, create_context, use_context
from idom.core.layout import Layout, LayoutEvent
from idom.core.serve import VdomJsonPatch, serve_json_patch
from idom.core.types import ComponentConstructor

from .utils import CLIENT_BUILD_DIR


RequestContext: type[Context[HTTPServerRequest | None]] = create_context(
    None, "RequestContext"
)


def configure(
    app: Application,
    component: ComponentConstructor,
    options: Options | None = None,
) -> None:
    """Return a :class:`TornadoServer` where each client has its own state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        app: A tornado ``Application`` instance.
        component: A root component constructor
        options: Options for configuring how the component is mounted to the server.
    """
    options = options or Options()
    _add_handler(
        app,
        options,
        _setup_common_routes(options) + _setup_single_view_dispatcher_route(component),
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

    # setup up tornado to use asyncio
    AsyncIOMainLoop().install()

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


def use_request() -> HTTPServerRequest:
    """Get the current ``HTTPServerRequest``"""
    request = use_context(RequestContext)
    if request is None:
        raise RuntimeError(  # pragma: no cover
            "No request. Are you running with a Tornado server?"
        )
    return request


def use_scope() -> dict[str, Any]:
    """Get the current WSGI environment dictionary"""
    return WSGIContainer.environ(use_request())


@dataclass
class Options:
    """Render server options for :class:`TornadoRenderServer` subclasses"""

    redirect_root: bool = True
    """Whether to redirect the root URL (with prefix) to ``index.html``"""

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
                r"/client/(.*)",
                StaticFileHandler,
                {"path": str(CLIENT_BUILD_DIR)},
            )
        )
        handlers.append(
            (
                r"/modules/(.*)",
                StaticFileHandler,
                {"path": str(IDOM_WEB_MODULES_DIR.current)},
            )
        )
        if options.redirect_root:
            handlers.append(
                (
                    urljoin("/", options.url_prefix),
                    RedirectHandler,
                    {"url": "./client/index.html"},
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
            "/stream",
            ModelStreamHandler,
            {"component_constructor": constructor},
        )
    ]


class ModelStreamHandler(WebSocketHandler):
    """A web-socket handler that serves up a new model stream to each new client"""

    _dispatch_future: Future[None]
    _message_queue: AsyncQueue[str]

    def initialize(self, component_constructor: ComponentConstructor) -> None:
        self._component_constructor = component_constructor

    async def open(self, *args: str, **kwargs: str) -> None:
        message_queue: "AsyncQueue[str]" = AsyncQueue()

        async def send(value: VdomJsonPatch) -> None:
            await self.write_message(json.dumps(value))

        async def recv() -> LayoutEvent:
            return LayoutEvent(**json.loads(await message_queue.get()))

        self._message_queue = message_queue
        self._dispatch_future = asyncio.ensure_future(
            serve_json_patch(
                Layout(
                    RequestContext(self._component_constructor(), value=self.request)
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
