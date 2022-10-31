from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Union

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from idom.backend.hooks import ConnectionContext
from idom.backend.types import Connection, Location
from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.layout import Layout, LayoutEvent
from idom.core.serve import (
    RecvCoroutine,
    SendCoroutine,
    VdomJsonPatch,
    serve_json_patch,
)
from idom.core.types import RootComponentConstructor

from ._asgi import serve_development_asgi
from ._urls import ASSETS_PATH, MODULES_PATH, STREAM_PATH
from .hooks import ConnectionContext
from .hooks import use_connection as _use_connection
from .utils import CLIENT_BUILD_DIR


logger = logging.getLogger(__name__)


def configure(
    app: Starlette,
    constructor: RootComponentConstructor,
    options: Options | None = None,
) -> None:
    """Configure the necessary IDOM routes on the given app.

    Parameters:
        app: An application instance
        component: A component constructor
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
    return use_connection().carrier


def use_connection() -> Connection[WebSocket]:
    conn = _use_connection()
    if not isinstance(conn.carrier, WebSocket):
        raise TypeError(  # pragma: no cover
            f"Connection has unexpected carrier {conn.carrier}. "
            "Are you running with a Flask server?"
        )
    return conn


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
        app.mount(
            str(MODULES_PATH),
            StaticFiles(directory=IDOM_WEB_MODULES_DIR.current, check_dir=False),
        )
        app.mount(
            str(ASSETS_PATH),
            StaticFiles(directory=CLIENT_BUILD_DIR / "assets", check_dir=False),
        )
        # register this last so it takes least priority
        app.add_route(url_prefix + "/", serve_index)
        app.add_route(url_prefix + "/{path:path}", serve_index)


async def serve_index(request: Request) -> FileResponse:
    return FileResponse(CLIENT_BUILD_DIR / "index.html")


def _setup_single_view_dispatcher_route(
    options: Options, app: Starlette, constructor: RootComponentConstructor
) -> None:
    @app.websocket_route(str(STREAM_PATH))
    @app.websocket_route(f"{STREAM_PATH}/{{path:path}}")
    async def model_stream(socket: WebSocket) -> None:
        await socket.accept()
        send, recv = _make_send_recv_callbacks(socket)

        pathname = "/" + socket.scope["path_params"].get("path", "")
        pathname = pathname[len(options.url_prefix) :] or "/"
        search = socket.scope["query_string"].decode()

        try:
            await serve_json_patch(
                Layout(
                    ConnectionContext(
                        constructor(),
                        value=Connection(
                            scope=socket.scope,
                            location=Location(pathname, f"?{search}" if search else ""),
                            carrier=socket,
                        ),
                    )
                ),
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
