from __future__ import annotations

import logging
from collections.abc import Iterable
from importlib import import_module
from typing import Any

from asgiref import typing as asgi_types

from reactpy._option import Option
from reactpy.types import ReactPyConfig, VdomDict
from reactpy.utils import vdom_to_html

logger = logging.getLogger(__name__)


def import_dotted_path(dotted_path: str) -> Any:
    """Imports a dotted path and returns the callable."""
    if "." not in dotted_path:
        raise ValueError(f'"{dotted_path}" is not a valid dotted path.')

    module_name, component_name = dotted_path.rsplit(".", 1)

    try:
        module = import_module(module_name)
    except ImportError as error:
        msg = f'ReactPy failed to import "{module_name}"'
        raise ImportError(msg) from error

    try:
        return getattr(module, component_name)
    except AttributeError as error:
        msg = f'ReactPy failed to import "{component_name}" from "{module_name}"'
        raise AttributeError(msg) from error


def import_components(dotted_paths: Iterable[str]) -> dict[str, Any]:
    """Imports a list of dotted paths and returns the callables."""
    return {
        dotted_path: import_dotted_path(dotted_path) for dotted_path in dotted_paths
    }


def check_path(url_path: str) -> str:  # pragma: no cover
    """Check that a path is valid URL path."""
    if not url_path:
        return "URL path must not be empty."
    if not isinstance(url_path, str):
        return "URL path is must be a string."
    if not url_path.startswith("/"):
        return "URL path must start with a forward slash."
    if not url_path.endswith("/"):
        return "URL path must end with a forward slash."

    return ""


def dict_to_byte_list(
    data: dict[str, str | int],
) -> list[tuple[bytes, bytes]]:
    """Convert a dictionary to a list of byte tuples."""
    result: list[tuple[bytes, bytes]] = []
    for key, value in data.items():
        new_key = key.encode()
        new_value = value.encode() if isinstance(value, str) else str(value).encode()
        result.append((new_key, new_value))
    return result


def vdom_head_to_html(head: VdomDict) -> str:
    if isinstance(head, dict) and head.get("tagName") == "head":
        return vdom_to_html(head)

    raise ValueError(
        "Invalid head element! Element must be either `html.head` or a string."
    )


async def http_response(
    *,
    send: asgi_types.ASGISendCallable,
    method: str,
    code: int = 200,
    message: str = "",
    headers: Iterable[tuple[bytes, bytes]] = (),
) -> None:
    """Sends a HTTP response using the ASGI `send` API."""
    start_msg: asgi_types.HTTPResponseStartEvent = {
        "type": "http.response.start",
        "status": code,
        "headers": [*headers],
        "trailers": False,
    }
    body_msg: asgi_types.HTTPResponseBodyEvent = {
        "type": "http.response.body",
        "body": b"",
        "more_body": False,
    }

    # Add the content type and body to everything other than a HEAD request
    if method != "HEAD":
        body_msg["body"] = message.encode()

    await send(start_msg)
    await send(body_msg)


def process_settings(settings: ReactPyConfig) -> None:
    """Process the settings and return the final configuration."""
    from reactpy import config

    for setting in settings:
        config_name = f"REACTPY_{setting.upper()}"
        config_object: Option[Any] | None = getattr(config, config_name, None)
        if config_object:
            config_object.set_current(settings[setting])  # type: ignore
        else:
            raise ValueError(f'Unknown ReactPy setting "{setting}".')
