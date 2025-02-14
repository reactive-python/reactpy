from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from reactpy._option import Option
from reactpy.config import (
    REACTPY_PATH_PREFIX,
    REACTPY_RECONNECT_BACKOFF_MULTIPLIER,
    REACTPY_RECONNECT_INTERVAL,
    REACTPY_RECONNECT_MAX_INTERVAL,
    REACTPY_RECONNECT_MAX_RETRIES,
)
from reactpy.types import ReactPyConfig, VdomDict
from reactpy.utils import import_dotted_path, reactpy_to_string

logger = logging.getLogger(__name__)


def import_components(dotted_paths: Iterable[str]) -> dict[str, Any]:
    """Imports a list of dotted paths and returns the callables."""
    return {
        dotted_path: import_dotted_path(dotted_path) for dotted_path in dotted_paths
    }


def check_path(url_path: str) -> str:  # nocov
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


def vdom_head_to_html(head: VdomDict) -> str:
    if isinstance(head, dict) and head.get("tagName") == "head":
        return reactpy_to_string(head)

    raise ValueError(
        "Invalid head element! Element must be either `html.head` or a string."
    )


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


def server_side_component_html(
    element_id: str, class_: str, component_path: str
) -> str:
    return (
        f'<div id="{element_id}" class="{class_}"></div>'
        '<script type="module" crossorigin="anonymous">'
        f'import {{ mountReactPy }} from "{REACTPY_PATH_PREFIX.current}static/index.js";'
        "mountReactPy({"
        f' mountElement: document.getElementById("{element_id}"),'
        f' pathPrefix: "{REACTPY_PATH_PREFIX.current}",'
        f' componentPath: "{component_path}",'
        f" reconnectInterval: {REACTPY_RECONNECT_INTERVAL.current},"
        f" reconnectMaxInterval: {REACTPY_RECONNECT_MAX_INTERVAL.current},"
        f" reconnectMaxRetries: {REACTPY_RECONNECT_MAX_RETRIES.current},"
        f" reconnectBackoffMultiplier: {REACTPY_RECONNECT_BACKOFF_MULTIPLIER.current},"
        "});"
        "</script>"
    )
