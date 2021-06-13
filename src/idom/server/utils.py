import asyncio
import time
from contextlib import closing
from functools import wraps
from importlib import import_module
from pathlib import Path
from socket import socket
from threading import Event, Thread
from typing import Any, Callable, List, Optional, TypeVar, cast

import idom

from .proto import ServerFactory


CLIENT_BUILD_DIR = Path(idom.__file__).parent / "client" / "build"

_SUPPORTED_PACKAGES = [
    "sanic",
    "fastapi",
    "flask",
    "tornado",
]

_Func = TypeVar("_Func", bound=Callable[..., None])


def threaded(function: _Func) -> _Func:
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        def target() -> None:
            asyncio.set_event_loop(asyncio.new_event_loop())
            function(*args, **kwargs)

        Thread(target=target, daemon=True).start()

        return None

    return cast(_Func, wrapper)


def wait_on_event(description: str, event: Event, timeout: Optional[float]) -> None:
    if not event.wait(timeout):
        raise TimeoutError(f"Did not {description} within {timeout} seconds")


def poll(
    description: str,
    frequency: float,
    timeout: Optional[float],
    function: Callable[[], bool],
) -> None:
    if timeout is not None:
        expiry = time.time() + timeout
        while not function():
            if time.time() > expiry:
                raise TimeoutError(f"Did not {description} within {timeout} seconds")
            time.sleep(frequency)
    else:
        while not function():
            time.sleep(frequency)


def find_builtin_server_type(type_name: str) -> ServerFactory[Any, Any]:
    """Find first installed server implementation

    Raises:
        :class:`RuntimeError` if one cannot be found
    """
    installed_builtins: List[str] = []
    for name in _SUPPORTED_PACKAGES:
        try:
            import_module(name)
        except ImportError:  # pragma: no cover
            continue
        else:
            builtin_module = import_module(f"idom.server.{name}")
            installed_builtins.append(builtin_module.__name__)
        try:
            return getattr(builtin_module, type_name)  # type: ignore
        except AttributeError:  # pragma: no cover
            pass
    else:  # pragma: no cover
        if not installed_builtins:
            raise RuntimeError(
                f"Found none of the following builtin server implementations {_SUPPORTED_PACKAGES}"
            )
        else:
            raise ImportError(
                f"No server type {type_name!r} found in installed implementations {installed_builtins}"
            )


def find_available_port(host: str, port_min: int = 8000, port_max: int = 9000) -> int:
    """Get a port that's available for the given host and port range"""
    for port in range(port_min, port_max):
        with closing(socket()) as sock:
            try:
                sock.bind((host, port))
            except OSError:
                pass
            else:
                return port
    raise RuntimeError(
        f"Host {host!r} has no available port in range {port_max}-{port_max}"
    )
