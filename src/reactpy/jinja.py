import urllib.parse
from importlib import import_module
from typing import ClassVar
from uuid import uuid4

from jinja2_simple_tags import StandaloneTag

from reactpy.config import (
    REACTPY_PATH_PREFIX,
    REACTPY_RECONNECT_BACKOFF_MULTIPLIER,
    REACTPY_RECONNECT_INTERVAL,
    REACTPY_RECONNECT_MAX_INTERVAL,
    REACTPY_RECONNECT_MAX_RETRIES,
)

try:
    import_module("jinja2")
except ImportError as e:
    raise ImportError(
        "The Jinja2 library is required to use the ReactPy template tag. "
        "Please install it via `pip install reactpy[jinja]`."
    ) from e


class ReactPyTemplateTag(StandaloneTag):
    """This allows enables a `component` tag to be used in any Jinja2 rendering context."""

    safe_output = True
    tags: ClassVar[set[str]] = {"component"}

    def render(self, dotted_path: str, *args, **kwargs):
        uuid = uuid4().hex
        class_ = kwargs.pop("class", "")
        kwargs.pop("key", "")  # `key` is effectively useless for the root node

        # Generate the websocket URL
        append_component_path = f"{dotted_path}/"
        if kwargs.get("args") is not None:
            raise ValueError("Cannot specify `args` as a keyword argument")
        if args:
            kwargs["args"] = args
        if kwargs:
            append_component_path += f"?{urllib.parse.urlencode(kwargs)}"

        # TODO: Turn this into a util function and maybe use it for the standalone version too?
        return (
            f'<div id="{uuid}" class="{class_}"></div>'
            '<script type="module" crossorigin="anonymous">'
            f'import {{ mountReactPy }} from "{REACTPY_PATH_PREFIX.current}static/index.js";'
            "mountReactPy({"
            f'   mountElement: document.getElementById("{uuid}"),'
            f'   pathPrefix: "{REACTPY_PATH_PREFIX.current}",'
            f'   appendComponentPath: "{append_component_path}",'
            f"   reconnectInterval: {REACTPY_RECONNECT_INTERVAL.current},"
            f"   reconnectMaxInterval: {REACTPY_RECONNECT_MAX_INTERVAL.current},"
            f"   reconnectMaxRetries: {REACTPY_RECONNECT_MAX_RETRIES.current},"
            f"   reconnectBackoffMultiplier: {REACTPY_RECONNECT_BACKOFF_MULTIPLIER.current},"
            "});"
            "</script>"
        )
