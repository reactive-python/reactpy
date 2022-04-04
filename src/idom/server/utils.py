from __future__ import annotations

import asyncio
import logging
import socket
from contextlib import closing
from importlib import import_module
from pathlib import Path
from typing import Any, Iterator

from werkzeug.security import safe_join

import idom
from idom.config import IDOM_WEB_MODULES_DIR
from idom.types import RootComponentConstructor

from .types import ServerImplementation


logger = logging.getLogger(__name__)
CLIENT_BUILD_DIR = Path(idom.__file__).parent / "client"

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
    implementation: ServerImplementation[Any] | None = None,
) -> None:
    """Run a component with a development server"""
    logger.warn(
        "You are running a development server. "
        "Change this before deploying in production!"
    )

    implementation = implementation or import_module("idom.server.default")

    app = implementation.create_development_app()
    implementation.configure(app, component)

    host = host
    port = port or find_available_port(host)

    app_cls = type(app)
    logger.info(
        f"Running with {app_cls.__module__}.{app_cls.__name__} at http://{host}:{port}"
    )

    asyncio.get_event_loop().run_until_complete(
        implementation.serve_development_app(app, host, port)
    )


def safe_client_build_dir_path(path: str) -> Path:
    """Prevent path traversal out of :data:`CLIENT_BUILD_DIR`"""
    start, _, end = path.rpartition("/")
    file = end or start
    final_path = traversal_safe_path(CLIENT_BUILD_DIR, file)
    return final_path if final_path.is_file() else (CLIENT_BUILD_DIR / "index.html")


def safe_web_modules_dir_path(path: str) -> Path:
    """Prevent path traversal out of :data:`idom.config.IDOM_WEB_MODULES_DIR`"""
    return traversal_safe_path(IDOM_WEB_MODULES_DIR.current, *path.split("/"))


def traversal_safe_path(root: Path, *unsafe_parts: str | Path) -> Path:
    """Sanitize user given path using ``werkzeug.security.safe_join``"""
    path = safe_join(str(root.resolve()), *unsafe_parts)
    if path is None:
        raise ValueError("Unsafe path")  # pragma: no cover
    return Path(path)


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
