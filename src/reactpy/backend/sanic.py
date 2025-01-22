from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib import parse as urllib_parse
from uuid import uuid4

from sanic import Blueprint, Sanic, request, response
from sanic.config import Config
from sanic.server.websockets.connection import WebSocketConnection
from sanic_cors import CORS

from reactpy.backend._common import (
    ASSETS_PATH,
    MODULES_PATH,
    PATH_PREFIX,
    STREAM_PATH,
    CommonOptions,
    read_client_index_html,
    safe_client_build_dir_path,
    safe_web_modules_dir_path,
    serve_with_uvicorn,
)
from reactpy.backend.types import Connection, Location
from reactpy.core.hooks import ConnectionContext
from reactpy.core.hooks import use_connection as _use_connection
from reactpy.core.layout import Layout
from reactpy.core.serve import RecvCoroutine, SendCoroutine, Stop, serve_layout
from reactpy.core.types import RootComponentConstructor

logger = logging.getLogger(__name__)


# BackendType.Options
@dataclass
class Options(CommonOptions):
    """Render server config for :func:`reactpy.backend.sanic.configure`"""

    cors: bool | dict[str, Any] = False
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``sanic_cors.CORS``
    """


# BackendType.configure
def configure(
    app: Sanic[Any, Any],
    component: RootComponentConstructor,
    options: Options | None = None,
) -> None:
    """Configure an application instance to display the given component"""
    options = options or Options()

    spa_bp = Blueprint(f"reactpy_spa_{id(app)}", url_prefix=options.url_prefix)
    api_bp = Blueprint(f"reactpy_api_{id(app)}", url_prefix=str(PATH_PREFIX))

    _setup_common_routes(api_bp, spa_bp, options)
    _setup_single_view_dispatcher_route(api_bp, component, options)

    app.blueprint([spa_bp, api_bp])


# BackendType.create_development_app
def create_development_app() -> Sanic[Any, Any]:
    """Return a :class:`Sanic` app instance in test mode"""
    Sanic.test_mode = True
    logger.warning("Sanic.test_mode is now active")
    return Sanic(f"reactpy_development_app_{uuid4().hex}", Config())


# BackendType.serve_development_app
async def serve_development_app(
    app: Sanic[Any, Any],
    host: str,
    port: int,
    started: asyncio.Event | None = None,
) -> None:
    """Run a development server for :mod:`sanic`"""
    await serve_with_uvicorn(app, host, port, started)


def use_request() -> request.Request[Any, Any]:
    """Get the current ``Request``"""
    return use_connection().carrier.request


def use_websocket() -> WebSocketConnection:
    """Get the current websocket"""
    return use_connection().carrier.websocket


def use_connection() -> Connection[_SanicCarrier]:
    """Get the current :class:`Connection`"""
    conn = _use_connection()
    if not isinstance(conn.carrier, _SanicCarrier):  # nocov
        msg = f"Connection has unexpected carrier {conn.carrier}. Are you running with a Sanic server?"
        raise TypeError(msg)
    return conn


def _setup_common_routes(
    api_blueprint: Blueprint,
    spa_blueprint: Blueprint,
    options: Options,
) -> None:
    cors_options = options.cors
    if cors_options:  # nocov
        cors_params = cors_options if isinstance(cors_options, dict) else {}
        CORS(api_blueprint, **cors_params)

    index_html = read_client_index_html(options)

    async def single_page_app_files(
        request: request.Request[Any, Any],
        _: str = "",
    ) -> response.HTTPResponse:
        return response.html(index_html)

    if options.serve_index_route:
        spa_blueprint.add_route(
            single_page_app_files,
            "/",
            name="single_page_app_files_root",
        )
        spa_blueprint.add_route(
            single_page_app_files,
            "/<_:path>",
            name="single_page_app_files_path",
        )

    async def asset_files(
        request: request.Request[Any, Any],
        path: str = "",
    ) -> response.HTTPResponse:
        path = urllib_parse.unquote(path)
        return await response.file(safe_client_build_dir_path(f"assets/{path}"))

    api_blueprint.add_route(asset_files, f"/{ASSETS_PATH.name}/<path:path>")

    async def web_module_files(
        request: request.Request[Any, Any],
        path: str,
        _: str = "",  # this is not used
    ) -> response.HTTPResponse:
        path = urllib_parse.unquote(path)
        return await response.file(
            safe_web_modules_dir_path(path),
            mime_type="text/javascript",
        )

    api_blueprint.add_route(web_module_files, f"/{MODULES_PATH.name}/<path:path>")


def _setup_single_view_dispatcher_route(
    api_blueprint: Blueprint,
    constructor: RootComponentConstructor,
    options: Options,
) -> None:
    async def model_stream(
        request: request.Request[Any, Any],
        socket: WebSocketConnection,
        path: str = "",
    ) -> None:
        asgi_app = getattr(request.app, "_asgi_app", None)
        scope = asgi_app.transport.scope if asgi_app else {}
        if not scope:  # nocov
            logger.warning("No scope. Sanic may not be running with an ASGI server")

        send, recv = _make_send_recv_callbacks(socket)
        await serve_layout(
            Layout(
                ConnectionContext(
                    constructor(),
                    value=Connection(
                        scope=scope,
                        location=Location(
                            pathname=f"/{path[len(options.url_prefix):]}",
                            search=(
                                f"?{request.query_string}"
                                if request.query_string
                                else ""
                            ),
                        ),
                        carrier=_SanicCarrier(request, socket),
                    ),
                )
            ),
            send,
            recv,
        )

    api_blueprint.add_websocket_route(
        model_stream,
        f"/{STREAM_PATH.name}",
        name="model_stream_root",
    )
    api_blueprint.add_websocket_route(
        model_stream,
        f"/{STREAM_PATH.name}/<path:path>/",
        name="model_stream_path",
    )


def _make_send_recv_callbacks(
    socket: WebSocketConnection,
) -> tuple[SendCoroutine, RecvCoroutine]:
    async def sock_send(value: Any) -> None:
        await socket.send(json.dumps(value))

    async def sock_recv() -> Any:
        data = await socket.recv()
        if data is None:
            raise Stop()
        return json.loads(data)

    return sock_send, sock_recv


@dataclass
class _SanicCarrier:
    """A simple wrapper for holding connection information"""

    request: request.Request[Sanic[Any, Any], Any]
    """The current request object"""

    websocket: WebSocketConnection
    """A handle to the current websocket"""
