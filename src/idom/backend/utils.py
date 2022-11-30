from __future__ import annotations

import asyncio
import logging
import socket
from contextlib import closing
from importlib import import_module
from typing import Any, Iterator

from idom.types import RootComponentConstructor

from .types import BackendImplementation


logger = logging.getLogger(__name__)

SUPPORTED_PACKAGES = (
    "starlette",
    "fastapi",
    "sanic",
    "tornado",
    "flask",
)


def run(
    component: RootComponentConstructor,
    host: str = "127.0.0.1",
    port: int | None = None,
    implementation: BackendImplementation[Any] | None = None,
) -> None:
    """Run a component with a development server"""
    logger.warning(_DEVELOPMENT_RUN_FUNC_WARNING)

    implementation = implementation or import_module("idom.backend.default")

    app = implementation.create_development_app()
    implementation.configure(app, component)

    host = host
    port = port or find_available_port(host)

    app_cls = type(app)
    logger.info(
        f"Running with {app_cls.__module__}.{app_cls.__name__} at http://{host}:{port}"
    )

    asyncio.run(implementation.serve_development_app(app, host, port))


def find_available_port(
    host: str,
    port_min: int = 8000,
    port_max: int = 9000,
    allow_reuse_waiting_ports: bool = True,
) -> int:
    """Get a port that's available for the given host and port range"""
    for port in range(port_min, port_max):
        with closing(socket.socket()) as sock:
            try:
                if allow_reuse_waiting_ports:
                    # As per this answer: https://stackoverflow.com/a/19247688/3159288
                    # setting can be somewhat unreliable because we allow the use of
                    # ports that are stuck in TIME_WAIT. However, not setting the option
                    # means we're overly cautious and almost always use a different addr
                    # even if it could have actually been used.
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
            except OSError:
                pass
            else:
                return port
    raise RuntimeError(
        f"Host {host!r} has no available port in range {port_max}-{port_max}"
    )


def all_implementations() -> Iterator[BackendImplementation[Any]]:
    """Yield all available server implementations"""
    for name in SUPPORTED_PACKAGES:
        try:
            relative_import_name = f"{__name__.rsplit('.', 1)[0]}.{name}"
            module = import_module(relative_import_name)
        except ImportError:  # pragma: no cover
            logger.debug(f"Failed to import {name!r}", exc_info=True)
            continue

        if not isinstance(module, BackendImplementation):
            raise TypeError(  # pragma: no cover
                f"{module.__name__!r} is an invalid implementation"
            )

        yield module


_DEVELOPMENT_RUN_FUNC_WARNING = f"""\
The `run()` function is only intended for testing during development! To run in \
production, consider selecting a supported backend and importing its associated \
`configure()` function from `idom.backend.<package>` where `<package>` is one of \
{list(SUPPORTED_PACKAGES)}. For details refer to the docs on how to run each package.\
"""
