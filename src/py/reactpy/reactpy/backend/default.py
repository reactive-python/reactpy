from __future__ import annotations

import asyncio
from logging import getLogger
from sys import exc_info
from typing import Any, NoReturn

from reactpy.backend.types import BackendType
from reactpy.backend.utils import SUPPORTED_BACKENDS, all_implementations
from reactpy.types import RootComponentConstructor

logger = getLogger(__name__)
_DEFAULT_IMPLEMENTATION: BackendType[Any] | None = None


# BackendType.Options
class Options:  # nocov
    """Configuration options that can be provided to the backend.
    This definition should not be used/instantiated. It exists only for
    type hinting purposes."""

    def __init__(self, *args: Any, **kwds: Any) -> NoReturn:
        msg = "Default implementation has no options."
        raise ValueError(msg)


# BackendType.configure
def configure(
    app: Any, component: RootComponentConstructor, options: None = None
) -> None:
    """Configure the given app instance to display the given component"""
    if options is not None:  # nocov
        msg = "Default implementation cannot be configured with options"
        raise ValueError(msg)
    return _default_implementation().configure(app, component)


# BackendType.create_development_app
def create_development_app() -> Any:
    """Create an application instance for development purposes"""
    return _default_implementation().create_development_app()


# BackendType.serve_development_app
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


def _default_implementation() -> BackendType[Any]:
    """Get the first available server implementation"""
    global _DEFAULT_IMPLEMENTATION  # noqa: PLW0603

    if _DEFAULT_IMPLEMENTATION is not None:
        return _DEFAULT_IMPLEMENTATION

    try:
        implementation = next(all_implementations())
    except StopIteration:  # nocov
        logger.debug("Backend implementation import failed", exc_info=exc_info())
        supported_backends = ", ".join(SUPPORTED_BACKENDS)
        msg = (
            "It seems you haven't installed a backend. To resolve this issue, "
            "you can install a backend by running:\n\n"
            '\033[1mpip install "reactpy[starlette]"\033[0m\n\n'
            f"Other supported backends include: {supported_backends}."
        )
        raise RuntimeError(msg) from None
    else:
        _DEFAULT_IMPLEMENTATION = implementation
        return implementation
