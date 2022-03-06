from __future__ import annotations

import asyncio
import warnings
import webbrowser
from importlib import import_module
from typing import Any, Awaitable, TypeVar, runtime_checkable

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


def develop(
    component: ComponentConstructor,
    app: Any | None = None,
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

    implementation = _get_implementation(app)

    if app is None:
        app = implementation.create_development_app()

    implementation.configure_development_view(component)

    coros: list[Awaitable] = []

    host = host
    port = port or find_available_port(host)
    server_did_start = asyncio.Event()

    coros.append(
        implementation.serve_development_app(
            app,
            host=host,
            port=port,
            did_start=server_did_start,
        )
    )

    if open_browser:
        coros.append(_open_browser_after_server(host, port, server_did_start))

    asyncio.get_event_loop().run_forever(asyncio.gather(*coros))


async def _open_browser_after_server(
    host: str,
    port: int,
    server_did_start: asyncio.Event,
) -> None:
    await server_did_start.wait()
    webbrowser.open(f"http://{host}:{port}")


def _get_implementation(app: _App | None) -> _Implementation:
    implementations = _all_implementations()

    if app is None:
        return next(iter(implementations.values()))

    for cls in type(app).mro():
        if cls in implementations:
            return implementations[cls]
    else:
        raise TypeError(f"No built-in and installed implementation supports {app}")


def _all_implementations() -> dict[type[Any], _Implementation]:
    if not _INSTALLED_IMPLEMENTATIONS:
        for name in SUPPORTED_PACKAGES:
            try:
                module = import_module(f"idom.server.{name}")
            except ImportError:  # pragma: no cover
                continue

            if not isinstance(module, _Implementation):
                raise TypeError(f"{module.__name__!r} is an invalid implementation")

            _INSTALLED_IMPLEMENTATIONS[module.SERVER_TYPE] = module

    if not _INSTALLED_IMPLEMENTATIONS:
        raise RuntimeError("No built-in implementations are installed")

    return _INSTALLED_IMPLEMENTATIONS


_App = TypeVar("_App")


@runtime_checkable
class _Implementation(Protocol):

    APP_TYPE = type[Any]

    def create_development_app(self) -> Any:
        ...

    def configure_development_view(self, component: ComponentConstructor) -> None:
        ...

    async def serve_development_app(
        self,
        app: Any,
        host: str,
        port: int,
        did_start: asyncio.Event,
    ) -> None:
        ...


_INSTALLED_IMPLEMENTATIONS: dict[type[Any], _Implementation[Any]] = {}
