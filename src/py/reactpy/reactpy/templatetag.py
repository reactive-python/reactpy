from jinja2_simple_tags import StandaloneTag
from uuid import uuid4
import urllib.parse

REACTPY_WEBSOCKET_URL: str
REACTPY_WEB_MODULES_URL: str
REACTPY_RECONNECT_MAX: str
REACTPY_CLIENT_URL: str


class ComponentTag(StandaloneTag):
    """This allows enables a `component` tag to be used in any Jinja2 rendering context."""
    safe_output = True
    tags = {"component"}

    def render(self, dotted_path: str, *args, **kwargs):
        uuid = uuid4().hex
        class_ = kwargs.pop("class", "")
        kwargs.pop("key", "")  # `key` is effectively useless for the root node

        # Generate the websocket URL
        # TODO: This will require rewriting the websocket URL to `reactpy-ws/<uuid>?<kwargs>`
        component_ws_url = f"{REACTPY_WEBSOCKET_URL}/{uuid}"
        if kwargs.get("args") is not None:
            raise ValueError("Cannot specify `args` as a keyword argument")
        if args:
            kwargs["args"] = args
        if kwargs:
            component_ws_url += f"?{urllib.parse.urlencode(kwargs)}"

        return (
            f'<div id="{ uuid }" class="{ class_ }"></div>'
            '<script type="module" crossorigin="anonymous">'
            f'import {{ mountViewToElement }} from "{REACTPY_CLIENT_URL}";'
            f'const mountElement = document.getElementById("{ uuid }");'
            "mountViewToElement("
            "    mountElement,"
            f'   "{ component_ws_url }",'
            f'   "{ REACTPY_WEB_MODULES_URL }",'
            f'   "{ REACTPY_RECONNECT_MAX }",'
            f'   "{ dotted_path }",'
            ");"
            "</script>"
        )
