from __future__ import annotations

import asyncio
import sys
import warnings
import webbrowser
from importlib import import_module
from typing import Any, Awaitable, Iterator

from idom.types import RootComponentConstructor

from .types import ServerImplementation
from .utils import find_available_port


SUPPORTED_PACKAGES = (
    "starlette",
    "fastapi",
    "sanic",
    "flask",
    "tornado",
)


def run(
    component: RootComponentConstructor,
    host: str = "127.0.0.1",
    port: int | None = None,
    open_browser: bool = True,
    implementation: ServerImplementation[Any] = sys.modules[__name__],
) -> None:
    """Run a component with a development server"""

    warnings.warn(
        "You are running a development server, be sure to change this before deploying in production!",
        UserWarning,
        stacklevel=2,
    )

    app = implementation.create_development_app()
    implementation.configure(app, component)

    coros: list[Awaitable[Any]] = []

    host = host
    port = port or find_available_port(host)
    started = asyncio.Event()

    coros.append(implementation.serve_development_app(app, host, port, started))

    if open_browser:

        async def _open_browser_after_server() -> None:
            await started.wait()
            webbrowser.open(f"http://{host}:{port}")

        coros.append(_open_browser_after_server())

    asyncio.get_event_loop().run_until_complete(asyncio.gather(*coros))


def configure(app: Any, component: RootComponentConstructor) -> None:
    """Configure the given app instance to display the given component"""
    return _get_any_implementation().configure(app, component)


def create_development_app() -> Any:
    """Create an application instance for development purposes"""
    return _get_any_implementation().create_development_app()


async def serve_development_app(
    app: Any, host: str, port: int, started: asyncio.Event
) -> None:
    """Run an application using a development server"""
    return await _get_any_implementation().serve_development_app(
        app, host, port, started
    )


def _get_any_implementation() -> ServerImplementation[Any]:
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


def all_implementations() -> Iterator[ServerImplementation[Any]]:
    """Yield all available server implementations"""
    for name in SUPPORTED_PACKAGES:
        try:
            module = import_module(f"idom.server.{name}")
        except ImportError:  # pragma: no cover
            continue

        if not isinstance(module, ServerImplementation):
            raise TypeError(  # pragma: no cover
                f"{module.__name__!r} is an invalid implementation"
            )

        yield module
