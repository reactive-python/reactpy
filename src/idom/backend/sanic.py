from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Union
from urllib import parse as urllib_parse
from uuid import uuid4

from sanic import Blueprint, Sanic, request, response
from sanic.config import Config
from sanic.models.asgi import ASGIScope
from sanic_cors import CORS
from websockets.legacy.protocol import WebSocketCommonProtocol

from idom.backend.types import Location
from idom.core.hooks import Context, create_context, use_context
from idom.core.layout import Layout, LayoutEvent
from idom.core.serve import (
    RecvCoroutine,
    SendCoroutine,
    Stop,
    VdomJsonPatch,
    serve_json_patch,
)
from idom.core.types import RootComponentConstructor

from ._asgi import serve_development_asgi
from .utils import safe_client_build_dir_path, safe_web_modules_dir_path


logger = logging.getLogger(__name__)

ConnectionContext: Context[Connection | None] = create_context(None)


def configure(
    app: Sanic, component: RootComponentConstructor, options: Options | None = None
) -> None:
    """Configure an application instance to display the given component"""
    options = options or Options()
    blueprint = Blueprint(f"idom_dispatcher_{id(app)}", url_prefix=options.url_prefix)

    _setup_common_routes(blueprint, options)

    # this route should take priority so set up it up first
    _setup_single_view_dispatcher_route(blueprint, component)

    app.blueprint(blueprint)


def create_development_app() -> Sanic:
    """Return a :class:`Sanic` app instance in debug mode"""
    return Sanic(f"idom_development_app_{uuid4().hex}", Config())


async def serve_development_app(
    app: Sanic,
    host: str,
    port: int,
    started: asyncio.Event | None = None,
) -> None:
    """Run a development server for :mod:`sanic`"""
    await serve_development_asgi(app, host, port, started)


def use_location() -> Location:
    """Get the current route as a string"""
    conn = use_connection()
    search = conn.request.query_string
    return Location(pathname="/" + conn.path, search="?" + search if search else "")


def use_scope() -> ASGIScope:
    """Get the current ASGI scope"""
    app = use_request().app
    try:
        asgi_app = app._asgi_app
    except AttributeError:  # pragma: no cover
        raise RuntimeError("No scope. Sanic may not be running with an ASGI server")
    return asgi_app.transport.scope


def use_request() -> request.Request:
    """Get the current ``Request``"""
    return use_connection().request


def use_connection() -> Connection:
    """Get the current :class:`Connection`"""
    connection = use_context(ConnectionContext)
    if connection is None:
        raise RuntimeError(  # pragma: no cover
            "No connection. Are you running with a Sanic server?"
        )
    return connection


@dataclass
class Connection:
    """A simple wrapper for holding connection information"""

    request: request.Request
    """The current request object"""

    websocket: WebSocketCommonProtocol
    """A handle to the current websocket"""

    path: str
    """The current path being served"""


@dataclass
class Options:
    """Options for :class:`SanicRenderServer`"""

    cors: Union[bool, Dict[str, Any]] = False
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``sanic_cors.CORS``
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

        async def single_page_app_files(
            request: request.Request,
            path: str = "",
        ) -> response.HTTPResponse:
            path = urllib_parse.unquote(path)
            return await response.file(safe_client_build_dir_path(path))

        blueprint.add_route(single_page_app_files, "/")
        blueprint.add_route(single_page_app_files, "/<path:path>")

        async def web_module_files(
            request: request.Request,
            path: str,
            _: str = "",  # this is not used
        ) -> response.HTTPResponse:
            path = urllib_parse.unquote(path)
            return await response.file(
                safe_web_modules_dir_path(path),
                mime_type="text/javascript",
            )

        blueprint.add_route(web_module_files, "/_api/modules/<path:path>")
        blueprint.add_route(web_module_files, "/<_:path>/_api/modules/<path:path>")


def _setup_single_view_dispatcher_route(
    blueprint: Blueprint, constructor: RootComponentConstructor
) -> None:
    async def model_stream(
        request: request.Request, socket: WebSocketCommonProtocol, path: str = ""
    ) -> None:
        send, recv = _make_send_recv_callbacks(socket)
        conn = Connection(request, socket, path)
        await serve_json_patch(
            Layout(ConnectionContext(constructor(), value=conn)),
            send,
            recv,
        )

    blueprint.add_websocket_route(model_stream, "/_api/stream")
    blueprint.add_websocket_route(model_stream, "/<path:path>/_api/stream")


def _make_send_recv_callbacks(
    socket: WebSocketCommonProtocol,
) -> Tuple[SendCoroutine, RecvCoroutine]:
    async def sock_send(value: VdomJsonPatch) -> None:
        await socket.send(json.dumps(value))

    async def sock_recv() -> LayoutEvent:
        data = await socket.recv()
        if data is None:
            raise Stop()
        return LayoutEvent(**json.loads(data))

    return sock_send, sock_recv
