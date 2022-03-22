from __future__ import annotations

import asyncio
from typing import Any

from idom.types import RootComponentConstructor

from .types import ServerImplementation
from .utils import all_implementations


def configure(app: Any, component: RootComponentConstructor) -> None:
    """Configure the given app instance to display the given component"""
    return _default_implementation().configure(app, component)


def create_development_app() -> Any:
    """Create an application instance for development purposes"""
    return _default_implementation().create_development_app()


async def serve_development_app(
    app: Any, host: str, port: int, started: asyncio.Event
) -> None:
    """Run an application using a development server"""
    return await _default_implementation().serve_development_app(
        app, host, port, started
    )


def use_connection() -> Any:
    return _default_implementation().use_connection()


def _default_implementation() -> ServerImplementation[Any]:
    """Get the first available server implementation"""
    global _DEFAULT_IMPLEMENTATION

    if _DEFAULT_IMPLEMENTATION is not None:
        return _DEFAULT_IMPLEMENTATION

    try:
        implementation = next(all_implementations())
    except StopIteration:
        raise RuntimeError("No built-in server implementation installed.")
    else:
        _DEFAULT_IMPLEMENTATION = implementation
        return implementation


_DEFAULT_IMPLEMENTATION: ServerImplementation[Any] | None = None
