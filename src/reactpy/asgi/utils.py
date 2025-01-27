from __future__ import annotations

import logging
from collections.abc import Coroutine, Iterable, Sequence
from importlib import import_module
from typing import Any, Callable

from reactpy.core.types import VdomDict
from reactpy.utils import vdom_to_html

logger = logging.getLogger(__name__)


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
    return {
        dotted_path: import_dotted_path(dotted_path) for dotted_path in dotted_paths
    }


def check_path(url_path: str) -> str:
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


def replace_many(content: str, replacements: dict[str, str]) -> str:
    """Find and replace several key-values, and throw and error if the substring is not found."""
    for key, value in replacements.items():
        if key not in content:
            raise ValueError(f"Could not find {key} in content")
        content = content.replace(key, value)
    return content


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
    send: Callable[[dict[str, Any]], Coroutine],
    method: str,
    code: int = 200,
    message: str = "",
    headers: Sequence = (),
) -> None:
    """Sends a HTTP response using the ASGI `send` API."""
    start_msg = {"type": "http.response.start", "status": code, "headers": [*headers]}
    body_msg: dict[str, str | bytes] = {"type": "http.response.body"}

    # Add the content type and body to everything other than a HEAD request
    if method != "HEAD":
        body_msg["body"] = message.encode()

    await send(start_msg)
    await send(body_msg)
