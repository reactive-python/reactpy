from __future__ import annotations

import asyncio
from logging import getLogger
from sys import exc_info
from typing import Any, NoReturn

from reactpy.backend.types import BackendImplementation
from reactpy.backend.utils import all_implementations
from reactpy.types import RootComponentConstructor

logger = getLogger(__name__)


def configure(
    app: Any, component: RootComponentConstructor, options: None = None
) -> None:
    """Configure the given app instance to display the given component"""
    if options is not None:  # nocov
        msg = "Default implementation cannot be configured with options"
        raise ValueError(msg)
    return _default_implementation().configure(app, component)


def create_development_app() -> Any:
    """Create an application instance for development purposes"""
    return _default_implementation().create_development_app()


def Options(*args: Any, **kwargs: Any) -> NoReturn:  # nocov
    """Create configuration options"""
    msg = "Default implementation has no options."
    raise ValueError(msg)


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
    global _DEFAULT_IMPLEMENTATION  # noqa: PLW0603

    if _DEFAULT_IMPLEMENTATION is not None:
        return _DEFAULT_IMPLEMENTATION

    try:
        implementation = next(all_implementations())
    except StopIteration:  # nocov
        logger.debug("Backend implementation import failed", exc_info=exc_info())
        msg = "No built-in server implementation installed."
        raise RuntimeError(msg) from None
    else:
        _DEFAULT_IMPLEMENTATION = implementation
        return implementation
