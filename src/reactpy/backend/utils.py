from __future__ import annotations

import asyncio
import logging
import socket
import sys
from collections.abc import Iterator
from contextlib import closing
from importlib import import_module
from typing import Any

from reactpy.backend.types import BackendType
from reactpy.types import RootComponentConstructor

logger = logging.getLogger(__name__)

SUPPORTED_BACKENDS = (
    "fastapi",
    "sanic",
    "tornado",
    "flask",
    "starlette",
)


def run(
    component: RootComponentConstructor,
    host: str = "127.0.0.1",
    port: int | None = None,
    implementation: BackendType[Any] | None = None,
) -> None:
    """Run a component with a development server"""
    logger.warning(_DEVELOPMENT_RUN_FUNC_WARNING)

    implementation = implementation or import_module("reactpy.backend.default")
    app = implementation.create_development_app()
    implementation.configure(app, component)
    port = port or find_available_port(host)
    app_cls = type(app)

    logger.info(
        "ReactPy is running with '%s.%s' at http://%s:%s",
        app_cls.__module__,
        app_cls.__name__,
        host,
        port,
    )
    asyncio.run(implementation.serve_development_app(app, host, port))


def find_available_port(host: str, port_min: int = 8000, port_max: int = 9000) -> int:
    """Get a port that's available for the given host and port range"""
    for port in range(port_min, port_max):
        with closing(socket.socket()) as sock:
            try:
                if sys.platform in ("linux", "darwin"):
                    # Fixes bug on Unix-like systems where every time you restart the
                    # server you'll get a different port on Linux. This cannot be set
                    # on Windows otherwise address will always be reused.
                    # Ref: https://stackoverflow.com/a/19247688/3159288
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
            except OSError:
                pass
            else:
                return port
    msg = f"Host {host!r} has no available port in range {port_max}-{port_max}"
    raise RuntimeError(msg)


def all_implementations() -> Iterator[BackendType[Any]]:
    """Yield all available server implementations"""
    for name in SUPPORTED_BACKENDS:
        try:
            import_module(name)
        except ImportError:  # nocov
            logger.debug("Failed to import %s", name, exc_info=True)
            continue

        reactpy_backend_name = f"{__name__.rsplit('.', 1)[0]}.{name}"
        yield import_module(reactpy_backend_name)


_DEVELOPMENT_RUN_FUNC_WARNING = """\
The `run()` function is only intended for testing during development! To run \
in production, refer to the docs on how to use reactpy.backend.*.configure.\
"""
