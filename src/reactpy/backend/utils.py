from __future__ import annotations

import logging
import re
import socket
import sys
from collections.abc import Iterable
from contextlib import closing
from importlib import import_module
from typing import Any

from reactpy.core.types import ComponentType
from reactpy.types import RootComponentConstructor

logger = logging.getLogger(__name__)


def run(
    component: RootComponentConstructor,
    host: str = "localhost",
    port: int | None = None,
) -> None:
    """Run a component with a development server"""
    logger.warning(
        "The `run()` function is only intended for testing purposes! To run in production, "
        "refer to ReactPy's documentation."
    )

    try:
        import uvicorn
    except ImportError as e:
        raise ImportError(
            "The `uvicorn` package is required to use `reactpy.run`. "
            "Please install it with `pip install uvicorn`."
        ) from e

    app = ...
    port = port or find_available_port(host)
    uvicorn.run(app, host=host, port=port)


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


def normalize_url_path(url: str) -> str:
    """Normalize a URL path."""
    new_url = re.sub(r"/+", "/", url)
    new_url = new_url.lstrip("/")
    new_url = new_url.rstrip("/")
    return new_url


def import_dotted_path(dotted_path: str) -> Any:
    """Imports a dotted path and returns the callable."""
    module_name, component_name = dotted_path.rsplit(".", 1)

    try:
        module = import_module(module_name)
    except ImportError as error:
        msg = f"Failed to import {module_name!r} while loading {component_name!r}"
        raise RuntimeError(msg) from error

    return getattr(module, component_name)


def import_components(dotted_paths: Iterable[str]) -> dict[str, Any]:
    """Imports a list of dotted paths and returns the callables."""
    results = {
        dotted_path: import_dotted_path(dotted_path) for dotted_path in dotted_paths
    }

    # Check that all imports are components
    for dotted_path, component in results.items():
        errors: list[str] = []
        if not isinstance(component, ComponentType):
            errors.append(
                f"Expected ComponentType, got {type(component)} for {dotted_path}"
            )
        if errors:
            raise RuntimeError(". ".join(errors))

    return results


def check_path(url_path: str) -> str:
    """Check that a path is valid URL path."""
    if not url_path:
        return "URL path must not be empty."
    if not isinstance(url_path, str):
        return "URL path is must be a string."
    if not url_path[0].isalnum():
        return "URL path must start with an alphanumeric character."

    return ""
