from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Tuple, Union

from mypy_extensions import TypedDict
from sanic import Blueprint, Sanic, request, response
from sanic_cors import CORS
from websockets import WebSocketCommonProtocol

from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.dispatcher import (
    RecvCoroutine,
    SendCoroutine,
    VdomJsonPatch,
    dispatch_single_view,
)
from idom.core.layout import Layout, LayoutEvent
from idom.core.types import RootComponentConstructor

from .utils import CLIENT_BUILD_DIR


logger = logging.getLogger(__name__)


def configure(
    app: Sanic, component: RootComponentConstructor, options: Options | None = None
) -> None:
    """Configure an application instance to display the given component"""
    options = _setup_options(options)
    blueprint = Blueprint(
        f"idom_dispatcher_{id(app)}", url_prefix=options["url_prefix"]
    )
    _setup_common_routes(blueprint, options)
    _setup_single_view_dispatcher_route(blueprint, component)
    app.blueprint(blueprint)


def create_development_app() -> Sanic:
    """Return a :class:`Sanic` app instance in debug mode"""
    return Sanic("idom_development_app")


async def serve_development_app(
    app: Sanic, host: str, port: int, started: asyncio.Event
) -> None:
    """Run a development server for :mod:`sanic`"""

    @app.listener("after_server_start")
    async def after_started():
        started.set()

    await app.create_server(host, port, debug=True)


class Options(TypedDict, total=False):
    """Options for :class:`SanicRenderServer`"""

    cors: Union[bool, Dict[str, Any]]
    """Enable or configure Cross Origin Resource Sharing (CORS)

    For more information see docs for ``sanic_cors.CORS``
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


def _setup_common_routes(blueprint: Blueprint, options: Options) -> None:
    cors_options = options["cors"]
    if cors_options:  # pragma: no cover
        cors_params = cors_options if isinstance(cors_options, dict) else {}
        CORS(blueprint, **cors_params)

    if options["serve_static_files"]:
        blueprint.static("/client", str(CLIENT_BUILD_DIR))
        blueprint.static("/modules", str(IDOM_WEB_MODULES_DIR.current))

        if options["redirect_root_to_index"]:

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
        component_params = {k: request.args.get(k) for k in request.args}
        await dispatch_single_view(Layout(constructor(**component_params)), send, recv)


def _make_send_recv_callbacks(
    socket: WebSocketCommonProtocol,
) -> Tuple[SendCoroutine, RecvCoroutine]:
    async def sock_send(value: VdomJsonPatch) -> None:
        await socket.send(json.dumps(value))

    async def sock_recv() -> LayoutEvent:
        return LayoutEvent(**json.loads(await socket.recv()))

    return sock_send, sock_recv
