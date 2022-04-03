from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Tuple, Union

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect

from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.hooks import Context, create_context, use_context
from idom.core.layout import Layout, LayoutEvent
from idom.core.serve import (
    RecvCoroutine,
    SendCoroutine,
    VdomJsonPatch,
    serve_json_patch,
)
from idom.core.types import RootComponentConstructor

from ._asgi import serve_development_asgi
from .utils import CLIENT_BUILD_DIR, client_build_dir_path


logger = logging.getLogger(__name__)

WebSocketContext: type[Context[WebSocket | None]] = create_context(
    None, "WebSocketContext"
)


def configure(
    app: Starlette,
    constructor: RootComponentConstructor,
    options: Options | None = None,
) -> None:
    """Return a :class:`StarletteServer` where each client has its own state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        app: An application instance
        constructor: A component constructor
        options: Options for configuring server behavior
    """
    options = options or Options()

    # this route should take priority so set up it up first
    _setup_single_view_dispatcher_route(options, app, constructor)

    _setup_common_routes(options, app)


def create_development_app() -> Starlette:
    """Return a :class:`Starlette` app instance in debug mode"""
    return Starlette(debug=True)


async def serve_development_app(
    app: Starlette,
    host: str,
    port: int,
    started: asyncio.Event | None = None,
) -> None:
    """Run a development server for starlette"""
    await serve_development_asgi(app, host, port, started)


def use_websocket() -> WebSocket:
    """Get the current WebSocket object"""
    websocket = use_context(WebSocketContext)
    if websocket is None:
        raise RuntimeError(  # pragma: no cover
            "No websocket. Are you running with a Starllette server?"
        )
    return websocket


def use_scope() -> Scope:
    """Get the current ASGI scope dictionary"""
    return use_websocket().scope


@dataclass
class Options:
    """Optionsuration options for :class:`StarletteRenderServer`"""

    cors: Union[bool, Dict[str, Any]] = False
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``starlette.middleware.cors.CORSMiddleware``
    """

    serve_static_files: bool = True
    """Whether or not to serve static files (i.e. web modules)"""

    url_prefix: str = ""
    """The URL prefix where IDOM resources will be served from"""


def _setup_common_routes(options: Options, app: Starlette) -> None:
    cors_options = options.cors
    if cors_options:  # pragma: no cover
        cors_params = (
            cors_options if isinstance(cors_options, dict) else {"allow_origins": ["*"]}
        )
        app.add_middleware(CORSMiddleware, **cors_params)

    # This really should be added to the APIRouter, but there's a bug in Starlette
    # BUG: https://github.com/tiangolo/fastapi/issues/1469
    url_prefix = options.url_prefix

    if options.serve_static_files:
        wm_dir = IDOM_WEB_MODULES_DIR.current
        web_module_files = StaticFiles(directory=wm_dir, html=True, check_dir=False)
        app.mount(url_prefix + "/_api/modules", web_module_files)
        app.mount(url_prefix + "/{_:path}/_api/modules", web_module_files)

        # register this last so it takes least priority
        app.mount(url_prefix + "/", single_page_app_files())


def single_page_app_files() -> Callable[..., Awaitable[None]]:
    static_files_app = StaticFiles(
        directory=CLIENT_BUILD_DIR,
        html=True,
        check_dir=False,
    )

    async def spa_app(scope: Scope, receive: Receive, send: Send) -> None:
        return await static_files_app(
            {**scope, "path": client_build_dir_path(scope["path"])},
            receive,
            send,
        )

    return spa_app


def _setup_single_view_dispatcher_route(
    options: Options, app: Starlette, constructor: RootComponentConstructor
) -> None:
    @app.websocket_route(options.url_prefix + "/_api/stream")
    @app.websocket_route(options.url_prefix + "/{path:path}/_api/stream")
    async def model_stream(socket: WebSocket) -> None:
        path_params: dict[str, str] = socket.scope["path_params"]
        path_params["path"] = "/" + path_params.get("path", "")

        await socket.accept()
        send, recv = _make_send_recv_callbacks(socket)
        try:
            await serve_json_patch(
                Layout(WebSocketContext(constructor(), value=socket)),
                send,
                recv,
            )
        except WebSocketDisconnect as error:
            logger.info(f"WebSocket disconnect: {error.code}")


def _make_send_recv_callbacks(
    socket: WebSocket,
) -> Tuple[SendCoroutine, RecvCoroutine]:
    async def sock_send(value: VdomJsonPatch) -> None:
        await socket.send_text(json.dumps(value))

    async def sock_recv() -> LayoutEvent:
        return LayoutEvent(**json.loads(await socket.receive_text()))

    return sock_send, sock_recv
