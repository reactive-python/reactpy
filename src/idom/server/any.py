from __future__ import annotations

import asyncio
import warnings
import webbrowser
from importlib import import_module
from typing import Any, Awaitable, Iterator, TypeVar, runtime_checkable

from typing_extensions import Protocol

from idom.types import ComponentConstructor

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

    try:
        implementation = next(all_implementations())
    except StopIteration:
        raise RuntimeError(  # pragma: no cover
            f"Found no built-in server implementation installed {SUPPORTED_PACKAGES}"
        )

    app = implementation.create_development_app()
    implementation.configure(app, component)

    coros: list[Awaitable] = []

    host = host
    port = port or find_available_port(host)
    started = asyncio.Event()

    coros.append(implementation.serve_development_app(app, host, port, started))

    if open_browser:

        async def _open_browser_after_server() -> None:
            await started.wait()
            webbrowser.open(f"http://{host}:{port}")

        coros.append(_open_browser_after_server())

    asyncio.get_event_loop().run_forever(asyncio.gather(*coros))


def configure(app: Any, component: ComponentConstructor) -> None:
    return get_implementation().configure(app, component)


def create_development_app() -> Any:
    return get_implementation().create_development_app()


async def serve_development_app(
    app: Any, host: str, port: int, started: asyncio.Event
) -> None:
    return await get_implementation().serve_development_app(app, host, port, started)


def get_implementation() -> Implementation:
    """Get the first available server implementation"""
    try:
        return next(all_implementations())
    except StopIteration:
        raise RuntimeError("No built-in server implementation installed.")


def all_implementations() -> Iterator[Implementation]:
    """Yield all available server implementations"""
    for name in SUPPORTED_PACKAGES:
        try:
            module = import_module(f"idom.server.{name}")
        except ImportError:  # pragma: no cover
            continue

        if not isinstance(module, Implementation):
            raise TypeError(f"{module.__name__!r} is an invalid implementation")

        yield module


_App = TypeVar("_App")


@runtime_checkable
class Implementation(Protocol):
    """Common interface for IDOM's builti-in server implementations"""

    def configure(self, app: _App, component: ComponentConstructor) -> None:
        """Configure the given app instance to display the given component"""

    def create_development_app(self) -> _App:
        """Create an application instance for development purposes"""

    async def serve_development_app(
        self, app: _App, host: str, port: int, started: asyncio.Event
    ) -> None:
        """Run an application using a development server"""
