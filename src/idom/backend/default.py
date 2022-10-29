from __future__ import annotations

import asyncio
from typing import Any, NoReturn

from idom.types import RootComponentConstructor

from .types import BackendImplementation
from .utils import all_implementations


def configure(
    app: Any, component: RootComponentConstructor, options: None = None
) -> None:
    """Configure the given app instance to display the given component"""
    if options is not None:  # pragma: no cover
        raise ValueError("Default implementation cannot be configured with options")
    return _default_implementation().configure(app, component)


def create_development_app() -> Any:
    """Create an application instance for development purposes"""
    return _default_implementation().create_development_app()


def Options(*args: Any, **kwargs: Any) -> NoReturn:
    """Create configuration options"""
    raise ValueError("Default implementation has no options.")  # pragma: no cover


async def serve_development_app(
    app: Any,
    host: str,
    port: int,
    started: asyncio.Event | None = None,
) -> None:
    """Run an application using a development server"""
    return await _default_implementation().serve_development_app(
        app, host, port, started
    )


_DEFAULT_IMPLEMENTATION: BackendImplementation[Any] | None = None


def _default_implementation() -> BackendImplementation[Any]:
    """Get the first available server implementation"""
    global _DEFAULT_IMPLEMENTATION

    if _DEFAULT_IMPLEMENTATION is not None:
        return _DEFAULT_IMPLEMENTATION

    try:
        implementation = next(all_implementations())
    except StopIteration:  # pragma: no cover
        raise RuntimeError("No built-in server implementation installed.")
    else:
        _DEFAULT_IMPLEMENTATION = implementation
        return implementation
