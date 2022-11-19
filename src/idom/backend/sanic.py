from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, MutableMapping, Tuple
from urllib import parse as urllib_parse
from uuid import uuid4

from sanic import Blueprint, Sanic, request, response
from sanic.config import Config
from sanic.server.websockets.connection import WebSocketConnection
from sanic_cors import CORS

from idom.backend.types import Connection, Location
from idom.core.layout import Layout, LayoutEvent
from idom.core.serve import (
    RecvCoroutine,
    SendCoroutine,
    Stop,
    VdomJsonPatch,
    serve_json_patch,
)
from idom.core.types import RootComponentConstructor

from ._common import (
    ASSETS_PATH,
    MODULES_PATH,
    PATH_PREFIX,
    STREAM_PATH,
    CommonOptions,
    read_client_index_html,
    safe_client_build_dir_path,
    safe_web_modules_dir_path,
    serve_development_asgi,
)
from .hooks import ConnectionContext
from .hooks import use_connection as _use_connection


logger = logging.getLogger(__name__)


def configure(
    app: Sanic, component: RootComponentConstructor, options: Options | None = None
) -> None:
    """Configure an application instance to display the given component"""
    options = options or Options()

    spa_bp = Blueprint(f"idom_spa_{id(app)}", url_prefix=options.url_prefix)
    api_bp = Blueprint(f"idom_api_{id(app)}", url_prefix=str(PATH_PREFIX))

    _setup_common_routes(api_bp, spa_bp, options)
    _setup_single_view_dispatcher_route(api_bp, component, options)

    app.blueprint([spa_bp, api_bp])


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


def use_request() -> request.Request:
    """Get the current ``Request``"""
    return use_connection().carrier.request


def use_websocket() -> WebSocketConnection:
    """Get the current websocket"""
    return use_connection().carrier.websocket


def use_connection() -> Connection[_SanicCarrier]:
    """Get the current :class:`Connection`"""
    conn = _use_connection()
    if not isinstance(conn.carrier, _SanicCarrier):
        raise TypeError(  # pragma: no cover
            f"Connection has unexpected carrier {conn.carrier}. "
            "Are you running with a Sanic server?"
        )
    return conn


@dataclass
class Options(CommonOptions):
    """Render server config for :func:`idom.backend.sanic.configure`"""

    cors: bool | dict[str, Any] = False
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``sanic_cors.CORS``
    """


def _setup_common_routes(
    api_blueprint: Blueprint,
    spa_blueprint: Blueprint,
    options: Options,
) -> None:
    cors_options = options.cors
    if cors_options:  # pragma: no cover
        cors_params = cors_options if isinstance(cors_options, dict) else {}
        CORS(api_blueprint, **cors_params)

    index_html = read_client_index_html(options)

    async def single_page_app_files(
        request: request.Request,
        _: str = "",
    ) -> response.HTTPResponse:
        return response.html(index_html)

    spa_blueprint.add_route(single_page_app_files, "/")
    spa_blueprint.add_route(single_page_app_files, "/<_:path>")

    async def asset_files(
        request: request.Request,
        path: str = "",
    ) -> response.HTTPResponse:
        path = urllib_parse.unquote(path)
        return await response.file(safe_client_build_dir_path(f"assets/{path}"))

    api_blueprint.add_route(asset_files, f"/{ASSETS_PATH.name}/<path:path>")

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

    api_blueprint.add_route(web_module_files, f"/{MODULES_PATH.name}/<path:path>")


def _setup_single_view_dispatcher_route(
    api_blueprint: Blueprint,
    constructor: RootComponentConstructor,
    options: Options,
) -> None:
    async def model_stream(
        request: request.Request, socket: WebSocketConnection, path: str = ""
    ) -> None:
        app = request.app
        try:
            asgi_app = app._asgi_app
        except AttributeError:  # pragma: no cover
            logger.warning("No scope. Sanic may not be running with an ASGI server")
            scope: MutableMapping[str, Any] = {}
        else:
            scope = asgi_app.transport.scope

        send, recv = _make_send_recv_callbacks(socket)
        await serve_json_patch(
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

    api_blueprint.add_websocket_route(model_stream, f"/{STREAM_PATH.name}")
    api_blueprint.add_websocket_route(model_stream, f"/{STREAM_PATH.name}/<path:path>/")


def _make_send_recv_callbacks(
    socket: WebSocketConnection,
) -> Tuple[SendCoroutine, RecvCoroutine]:
    async def sock_send(value: VdomJsonPatch) -> None:
        await socket.send(json.dumps(value))

    async def sock_recv() -> LayoutEvent:
        data = await socket.recv()
        if data is None:
            raise Stop()
        return LayoutEvent(**json.loads(data))

    return sock_send, sock_recv


@dataclass
class _SanicCarrier:
    """A simple wrapper for holding connection information"""

    request: request.Request
    """The current request object"""

    websocket: WebSocketConnection
    """A handle to the current websocket"""
