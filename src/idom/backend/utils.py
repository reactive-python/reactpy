from __future__ import annotations

import asyncio
import logging
import os
import socket
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Awaitable, Callable, Generic, Iterator, TypeVar

import idom
from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.hooks import create_context, use_context
from idom.types import RootComponentConstructor

from .types import BackendImplementation, SessionState


logger = logging.getLogger(__name__)
CLIENT_BUILD_DIR = Path(idom.__file__).parent / "_client"

SUPPORTED_PACKAGES = (
    "starlette",
    "fastapi",
    "sanic",
    "tornado",
    "flask",
)


SESSION_COOKIE_NAME = "IdomSessionId"


_State = TypeVar("_State")


class SessionManager(Generic[_State]):
    def __init__(
        self,
        create_state: Callable[[], Awaitable[_State]],
        read_state: Callable[[str], Awaitable[_State | None]],
        update_state: Callable[[_State], Awaitable[None]],
    ):
        self.context = create_context(None)
        self._create_state = create_state
        self._read_state = read_state
        self._update_state = update_state

    def use_context(self) -> _State:
        return use_context(self.context)

    async def update_state(self, state: SessionState[_State]) -> None:
        await self._update_state(state)
        logger.info(f"Updated session {state.id}")

    async def get_state(self, id: str | None = None) -> SessionState[_State] | None:
        if id is None:
            state = await self._create_state()
            logger.info(f"Created new session {state.id!r}")
        else:
            state = await self._read_state(id)
            if state is None:
                logger.info(f"Could not load session {id!r}")
                state = await self._create_state()
                logger.info(f"Created new session {state.id!r}")
            elif state.expiry_date < datetime.now(timezone.utc):
                logger.info(f"Session {id!r} expired at {state.expiry_date}")
                state = await self._create_state()
                logger.info(f"Created new session {state.id!r}")
            else:
                logger.info(f"Loaded existing session {id!r}")
        return state


def run(
    component: RootComponentConstructor,
    host: str = "127.0.0.1",
    port: int | None = None,
    implementation: BackendImplementation[Any] | None = None,
) -> None:
    """Run a component with a development server"""
    logger.warn(
        "You are running a development server. "
        "Change this before deploying in production!"
    )

    implementation = implementation or import_module("idom.backend.default")

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
    start, _, end = (path[:-1] if path.endswith("/") else path).rpartition("/")
    file = end or start
    final_path = traversal_safe_path(CLIENT_BUILD_DIR, file)
    return final_path if final_path.is_file() else (CLIENT_BUILD_DIR / "index.html")


def safe_web_modules_dir_path(path: str) -> Path:
    """Prevent path traversal out of :data:`idom.config.IDOM_WEB_MODULES_DIR`"""
    return traversal_safe_path(IDOM_WEB_MODULES_DIR.current, *path.split("/"))


def traversal_safe_path(root: str | Path, *unsafe: str | Path) -> Path:
    """Raise a ``ValueError`` if the ``unsafe`` path resolves outside the root dir."""
    root = os.path.abspath(root)

    # Resolve relative paths but not symlinks - symlinks should be ok since their
    # presence and where they point is under the control of the developer.
    path = os.path.abspath(os.path.join(root, *unsafe))

    if os.path.commonprefix([root, path]) != root:
        # If the common prefix is not root directory we resolved outside the root dir
        raise ValueError("Unsafe path")

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
