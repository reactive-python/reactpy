from __future__ import annotations

import asyncio
import json
from asyncio import Queue as AsyncQueue
from asyncio.futures import Future
from typing import Any, List, Tuple, Type, Union
from urllib.parse import urljoin

from tornado.httpserver import HTTPServer
from tornado.httputil import HTTPServerRequest
from tornado.log import enable_pretty_logging
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler
from tornado.wsgi import WSGIContainer

from idom.backend.types import Connection, Location
from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.layout import Layout, LayoutEvent
from idom.core.serve import VdomJsonPatch, serve_json_patch
from idom.core.types import ComponentConstructor

from ._common import (
    ASSETS_PATH,
    CLIENT_BUILD_DIR,
    MODULES_PATH,
    STREAM_PATH,
    CommonOptions,
    read_client_index_html,
)
from .hooks import ConnectionContext
from .hooks import use_connection as _use_connection


Options = CommonOptions
"""Render server config for :func:`idom.backend.tornado.configure`"""


def configure(
    app: Application,
    component: ComponentConstructor,
    options: CommonOptions | None = None,
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
            _setup_single_view_dispatcher_route(component, options)
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
    if not isinstance(conn.carrier, HTTPServerRequest):
        raise TypeError(  # pragma: no cover
            f"Connection has unexpected carrier {conn.carrier}. "
            "Are you running with a Flask server?"
        )
    return conn


_RouteHandlerSpecs = List[Tuple[str, Type[RequestHandler], Any]]


def _setup_common_routes(options: Options) -> _RouteHandlerSpecs:
    return [
        (
            rf"{MODULES_PATH}/(.*)",
            StaticFileHandler,
            {"path": str(IDOM_WEB_MODULES_DIR.current)},
        ),
        (
            rf"{ASSETS_PATH}/(.*)",
            StaticFileHandler,
            {"path": str(CLIENT_BUILD_DIR / "assets")},
        ),
        (
            r"/(.*)",
            IndexHandler,
            {"index_html": read_client_index_html(options)},
        ),
    ]


def _add_handler(
    app: Application, options: Options, handlers: _RouteHandlerSpecs
) -> None:
    prefixed_handlers: List[Any] = [
        (urljoin(options.url_prefix, route_pattern),) + tuple(handler_info)
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
                        value=Connection(
                            scope=WSGIContainer.environ(self.request),
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

    async def on_message(self, message: Union[str, bytes]) -> None:
        await self._message_queue.put(
            message if isinstance(message, str) else message.decode()
        )

    def on_close(self) -> None:
        if not self._dispatch_future.done():
            self._dispatch_future.cancel()
