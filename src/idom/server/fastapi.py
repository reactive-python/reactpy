from typing import Optional

from fastapi import FastAPI

from idom.core.types import ComponentConstructor

from .starlette import (
    Config,
    StarletteServer,
    _setup_common_routes,
    _setup_config_and_app,
    _setup_shared_view_dispatcher_route,
    _setup_single_view_dispatcher_route,
)


def PerClientStateServer(
    constructor: ComponentConstructor,
    config: Optional[Config] = None,
    app: Optional[FastAPI] = None,
) -> StarletteServer:
    """Return a :class:`StarletteServer` where each client has its own state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        constructor: A component constructor
        config: Options for configuring server behavior
        app: An application instance (otherwise a default instance is created)
    """
    config, app = _setup_config_and_app(config, app, FastAPI)
    _setup_common_routes(config, app)
    _setup_single_view_dispatcher_route(config["url_prefix"], app, constructor)
    return StarletteServer(app)


def SharedClientStateServer(
    constructor: ComponentConstructor,
    config: Optional[Config] = None,
    app: Optional[FastAPI] = None,
) -> StarletteServer:
    """Return a :class:`StarletteServer` where each client shares state.

    Implements the :class:`~idom.server.proto.ServerFactory` protocol

    Parameters:
        constructor: A component constructor
        config: Options for configuring server behavior
        app: An application instance (otherwise a default instance is created)
    """
    config, app = _setup_config_and_app(config, app, FastAPI)
    _setup_common_routes(config, app)
    _setup_shared_view_dispatcher_route(config["url_prefix"], app, constructor)
    return StarletteServer(app)
