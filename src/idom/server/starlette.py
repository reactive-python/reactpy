from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Union

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Scope
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
from .utils import CLIENT_BUILD_DIR


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
    _setup_common_routes(options, app)
    _setup_single_view_dispatcher_route(options.url_prefix, app, constructor)


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

    redirect_root: bool = True
    """Whether to redirect the root URL (with prefix) to ``index.html``"""

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
        app.mount(
            f"{url_prefix}/client",
            StaticFiles(
                directory=str(CLIENT_BUILD_DIR),
                html=True,
                check_dir=True,
            ),
            name="idom_client_files",
        )
        app.mount(
            f"{url_prefix}/modules",
            StaticFiles(
                directory=str(IDOM_WEB_MODULES_DIR.current),
                html=True,
                check_dir=False,
            ),
            name="idom_web_module_files",
        )

        if options.redirect_root:

            @app.route(f"{url_prefix}/")
            def redirect_to_index(request: Request) -> RedirectResponse:
                return RedirectResponse(
                    f"{url_prefix}/client/index.html?{request.query_params}"
                )


def _setup_single_view_dispatcher_route(
    url_prefix: str, app: Starlette, constructor: RootComponentConstructor
) -> None:
    @app.websocket_route(f"{url_prefix}/stream")
    async def model_stream(socket: WebSocket) -> None:
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
