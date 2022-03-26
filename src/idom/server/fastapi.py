from __future__ import annotations

from fastapi import FastAPI

from idom.config import IDOM_DEBUG_MODE
from idom.core.types import RootComponentConstructor

from .starlette import (
    Options,
    _setup_common_routes,
    _setup_options,
    _setup_single_view_dispatcher_route,
    serve_development_app,
    use_scope,
)


__all__ = (
    "configure",
    "serve_development_app",
    "create_development_app",
    "use_scope",
)


def configure(
    app: FastAPI,
    constructor: RootComponentConstructor,
    options: Options | None = None,
) -> None:
    """Prepare a :class:`FastAPI` server to serve the given component

    Parameters:
        app: An application instance
        constructor: A component constructor
        config: Options for configuring server behavior

    """
    options = _setup_options(options)
    _setup_common_routes(options, app)
    _setup_single_view_dispatcher_route(options["url_prefix"], app, constructor)


def create_development_app() -> FastAPI:
    return FastAPI(debug=IDOM_DEBUG_MODE.current)
