from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, replace
from typing import Any, Dict, Tuple, Union
from urllib import parse as urllib_parse
from uuid import uuid4

from sanic import Blueprint, Sanic, request, response
from sanic.config import Config
from sanic.models.asgi import ASGIScope
from sanic_cors import CORS
from websockets.legacy.protocol import WebSocketCommonProtocol

from idom.backend.types import Location, SessionState
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
from .utils import (
    SESSION_COOKIE_NAME,
    SessionManager,
    safe_client_build_dir_path,
    safe_web_modules_dir_path,
)


logger = logging.getLogger(__name__)

ConnectionContext: type[Context[Connection | None]] = create_context(
    None, "ConnectionContext"
)


def configure(
    app: Sanic, component: RootComponentConstructor, options: Options | None = None
) -> None:
    """Configure an application instance to display the given component"""
    options = options or Options()
    blueprint = Blueprint(f"idom_dispatcher_{id(app)}", url_prefix=options.url_prefix)

    _setup_common_routes(blueprint, options)

    # this route should take priority so set up it up first
    _setup_single_view_dispatcher_route(blueprint, component, options)

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

    session_manager: SessionManager[Any] | None = None
    """Used to create session cookies to perserve client state"""


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
    blueprint: Blueprint,
    constructor: RootComponentConstructor,
    options: Options,
) -> None:
    async def model_stream(
        request: request.Request, socket: WebSocketCommonProtocol, path: str = ""
    ) -> None:
        root = ConnectionContext(constructor(), value=Connection(request, socket, path))

        if options.session_manager:
            root = options.session_manager.context(
                root, value=request.ctx.idom_sesssion_state
            )

        send, recv = _make_send_recv_callbacks(socket)
        await serve_json_patch(Layout(root), send, recv)

    blueprint.add_websocket_route(model_stream, "/_api/stream")
    blueprint.add_websocket_route(model_stream, "/<path:path>/_api/stream")

    if options.session_manager:
        smgr = options.session_manager

        @blueprint.on_request
        async def set_session_on_request(request: request.Request) -> None:
            if request.scheme not in ("http", "https"):
                return
            session_id = request.cookies.get(SESSION_COOKIE_NAME)
            request.ctx.idom_session_state = await smgr.get_state(session_id)

        @blueprint.on_response
        async def set_session_cookie_header(
            request: request.Request, response: response.ResponseStream
        ):
            session_state: SessionState[Any] = request.ctx.idom_session_state
            # only set cookie if it has not been set before
            if session_state.fresh:
                # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie
                response.cookies[SESSION_COOKIE_NAME] = session_state.id
                response.cookies[SESSION_COOKIE_NAME]["secure"] = True
                response.cookies[SESSION_COOKIE_NAME]["httponly"] = True
                response.cookies[SESSION_COOKIE_NAME]["samesite"] = "strict"
                response.cookies[SESSION_COOKIE_NAME][
                    "expires"
                ] = session_state.expiry_date

                await smgr.update_state(replace(session_state, fresh=False))
                logger.info(f"Setting cookie {response.cookies[SESSION_COOKIE_NAME]}")


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
