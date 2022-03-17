from __future__ import annotations

import asyncio
import warnings
import webbrowser
from importlib import import_module
from typing import Any, Awaitable, Iterator

from idom.types import ComponentConstructor

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
    component: ComponentConstructor,
    host: str = "127.0.0.1",
    port: int | None = None,
    open_browser: bool = True,
) -> None:
    """Run a component with a development server"""

    warnings.warn(
        "You are running a development server, be sure to change this before deploying in production!",
        UserWarning,
        stacklevel=2,
    )

    app = create_development_app()
    configure(app, component)

    coros: list[Awaitable] = []

    host = host
    port = port or find_available_port(host)
    started = asyncio.Event()

    coros.append(serve_development_app(app, host, port, started))

    if open_browser:

        async def _open_browser_after_server() -> None:
            await started.wait()
            webbrowser.open(f"http://{host}:{port}")

        coros.append(_open_browser_after_server())

    asyncio.get_event_loop().run_forever(asyncio.gather(*coros))


def configure(app: Any, component: ComponentConstructor) -> None:
    """Configure the given app instance to display the given component"""
    return get_implementation().configure(app, component)


def create_development_app() -> Any:
    """Create an application instance for development purposes"""
    return get_implementation().create_development_app()


async def serve_development_app(
    app: Any, host: str, port: int, started: asyncio.Event
) -> None:
    """Run an application using a development server"""
    return await get_implementation().serve_development_app(app, host, port, started)


def get_implementation() -> ServerImplementation:
    """Get the first available server implementation"""
    if _DEFAULT_IMPLEMENTATION is not None:
        return _DEFAULT_IMPLEMENTATION

    try:
        implementation = next(all_implementations())
    except StopIteration:
        raise RuntimeError("No built-in server implementation installed.")
    else:
        global _DEFAULT_IMPLEMENTATION
        _DEFAULT_IMPLEMENTATION = implementation
        return implementation


_DEFAULT_IMPLEMENTATION: ServerImplementation | None = None


def all_implementations() -> Iterator[ServerImplementation]:
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
