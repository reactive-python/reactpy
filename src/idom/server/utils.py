import asyncio
import socket
import time
from contextlib import closing
from functools import wraps
from pathlib import Path
from threading import Event, Thread
from typing import Any, Callable, Optional

from typing_extensions import ParamSpec

import idom


CLIENT_BUILD_DIR = Path(idom.__file__).parent / "client"


_FuncParams = ParamSpec("_FuncParams")


def threaded(function: Callable[_FuncParams, None]) -> Callable[_FuncParams, Thread]:
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Thread:
        def target() -> None:
            asyncio.set_event_loop(asyncio.new_event_loop())
            function(*args, **kwargs)

        thread = Thread(target=target, daemon=True)
        thread.start()

        return thread

    return wrapper


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
