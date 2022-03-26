from __future__ import annotations

from fastapi import FastAPI

from idom.config import IDOM_DEBUG_MODE
from idom.core.types import RootComponentConstructor

from . import starlette


serve_development_app = starlette.serve_development_app
"""Alias for :func:`starlette.serve_development_app`"""

use_scope = starlette.use_scope
"""Alias for :func:`starlette.use_scope`"""

use_websocket = starlette.use_websocket
"""Alias for :func:`starlette.use_websocket`"""


def configure(
    app: FastAPI,
    constructor: RootComponentConstructor,
    options: starlette.Options | None = None,
) -> None:
    """Prepare a :class:`FastAPI` server to serve the given component

    Parameters:
        app: An application instance
        constructor: A component constructor
        config: Options for configuring server behavior
    """
    options = starlette._setup_options(options)
    starlette._setup_common_routes(options, app)
    starlette._setup_single_view_dispatcher_route(
        options["url_prefix"], app, constructor
    )


def create_development_app() -> FastAPI:
    return FastAPI(debug=IDOM_DEBUG_MODE.current)
