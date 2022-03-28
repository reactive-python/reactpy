from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Union
from uuid import uuid4

from sanic import Blueprint, Sanic, request, response
from sanic.config import Config
from sanic.models.asgi import ASGIScope
from sanic_cors import CORS
from websockets.legacy.protocol import WebSocketCommonProtocol

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

RequestContext: type[Context[request.Request | None]] = create_context(
    None, "RequestContext"
)


def configure(
    app: Sanic, component: RootComponentConstructor, options: Options | None = None
) -> None:
    """Configure an application instance to display the given component"""
    options = options or Options()
    blueprint = Blueprint(f"idom_dispatcher_{id(app)}", url_prefix=options.url_prefix)
    _setup_common_routes(blueprint, options)
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


def use_request() -> request.Request:
    """Get the current ``Request``"""
    request = use_context(RequestContext)
    if request is None:
        raise RuntimeError(  # pragma: no cover
            "No request. Are you running with a Sanic server?"
        )
    return request


def use_scope() -> ASGIScope:
    """Get the current ASGI scope"""
    app = use_request().app
    try:
        asgi_app = app._asgi_app
    except AttributeError:  # pragma: no cover
        raise RuntimeError("No scope. Sanic may not be running with an ASGI server")
    return asgi_app.transport.scope


@dataclass
class Options:
    """Options for :class:`SanicRenderServer`"""

    cors: Union[bool, Dict[str, Any]] = False
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``sanic_cors.CORS``
    """

    redirect_root: bool = True
    """Whether to redirect the root URL (with prefix) to ``index.html``"""

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
        blueprint.static("/client", str(CLIENT_BUILD_DIR))
        blueprint.static("/modules", str(IDOM_WEB_MODULES_DIR.current))

        if options.redirect_root:

            @blueprint.route("/")  # type: ignore
            def redirect_to_index(
                request: request.Request,
            ) -> response.HTTPResponse:
                return response.redirect(
                    f"{blueprint.url_prefix}/client/index.html?{request.query_string}"
                )


def _setup_single_view_dispatcher_route(
    blueprint: Blueprint, constructor: RootComponentConstructor
) -> None:
    @blueprint.websocket("/stream")  # type: ignore
    async def model_stream(
        request: request.Request, socket: WebSocketCommonProtocol
    ) -> None:
        send, recv = _make_send_recv_callbacks(socket)
        await serve_json_patch(
            Layout(RequestContext(constructor(), value=request)),
            send,
            recv,
        )


def _make_send_recv_callbacks(
    socket: WebSocketCommonProtocol,
) -> Tuple[SendCoroutine, RecvCoroutine]:
    async def sock_send(value: VdomJsonPatch) -> None:
        await socket.send(json.dumps(value))

    async def sock_recv() -> LayoutEvent:
        return LayoutEvent(**json.loads(await socket.recv()))

    return sock_send, sock_recv
