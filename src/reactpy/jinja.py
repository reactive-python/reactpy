import urllib.parse
from importlib import import_module
from typing import ClassVar
from uuid import uuid4

from jinja2_simple_tags import StandaloneTag

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

        # TODO: Fetch these from ReactPy settings
        client_js_path = "/reactpy/static/index.js"
        path_prefix = "/reactpy/"
        reconnect_interval = 750
        reconnect_max_interval = 60000
        reconnect_max_retries = 150
        reconnect_backoff_multiplier = 1.25

        # Generate the websocket URL
        # TODO: This will require rewriting the websocket URL to `reactpy-ws/<uuid>?<kwargs>`
        component_path = f"{dotted_path}/"
        if kwargs.get("args") is not None:
            raise ValueError("Cannot specify `args` as a keyword argument")
        if args:
            kwargs["args"] = args
        if kwargs:
            component_path += f"?{urllib.parse.urlencode(kwargs)}"

        # TODO: Turn this into a util function and maybe use it for the standalone version too?
        return (
            f'<div id="{uuid}" class="{class_}"></div>'
            '<script type="module" crossorigin="anonymous">'
            f'import {{ mountReactPy }} from "{client_js_path}";'
            f'const mountElement = document.getElementById("{uuid}");'
            "mountReactPy({"
            f'   mountElement: document.getElementById("{uuid}"),'
            f'   pathPrefix: "{path_prefix}",'
            f'   appendComponentPath: "{component_path}",'
            f"   reconnectInterval: {reconnect_interval},"
            f"   reconnectMaxInterval: {reconnect_max_interval},"
            f"   reconnectMaxRetries: {reconnect_max_retries},"
            f"   reconnectBackoffMultiplier: {reconnect_backoff_multiplier},"
            "});"
            "</script>"
        )
