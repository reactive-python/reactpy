from __future__ import annotations

import asyncio
import json
import logging
from asyncio import FIRST_EXCEPTION, CancelledError
from typing import Any, Dict, Tuple, Union

from mypy_extensions import TypedDict
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect
from uvicorn.config import Config as UvicornConfig
from uvicorn.server import Server as UvicornServer

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
from .utils import CLIENT_BUILD_DIR


logger = logging.getLogger(__name__)


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
    options = _setup_options(options)
    _setup_common_routes(options, app)
    _setup_single_view_dispatcher_route(options["url_prefix"], app, constructor)


def create_development_app() -> Starlette:
    """Return a :class:`Starlette` app instance in debug mode"""
    return Starlette(debug=True)


async def serve_development_app(
    app: Starlette,
    host: str,
    port: int,
    started: asyncio.Event,
) -> None:
    """Run a development server for starlette"""
    await serve_development_asgi(app, host, port, started)


class Options(TypedDict, total=False):
    """Optionsuration options for :class:`StarletteRenderServer`"""

    cors: Union[bool, Dict[str, Any]]
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``starlette.middleware.cors.CORSMiddleware``
    """

    redirect_root_to_index: bool
    """Whether to redirect the root URL (with prefix) to ``index.html``"""

    serve_static_files: bool
    """Whether or not to serve static files (i.e. web modules)"""

    url_prefix: str
    """The URL prefix where IDOM resources will be served from"""


def _setup_options(options: Options | None) -> Options:
    return {
        "cors": False,
        "url_prefix": "",
        "serve_static_files": True,
        "redirect_root_to_index": True,
        **(options or {}),  # type: ignore
    }


def _setup_common_routes(options: Options, app: Starlette) -> None:
    cors_options = options["cors"]
    if cors_options:  # pragma: no cover
        cors_params = (
            cors_options if isinstance(cors_options, dict) else {"allow_origins": ["*"]}
        )
        app.add_middleware(CORSMiddleware, **cors_params)

    # This really should be added to the APIRouter, but there's a bug in Starlette
    # BUG: https://github.com/tiangolo/fastapi/issues/1469
    url_prefix = options["url_prefix"]
    if options["serve_static_files"]:
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

        if options["redirect_root_to_index"]:

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
                Layout(constructor(**dict(socket.query_params))), send, recv
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
