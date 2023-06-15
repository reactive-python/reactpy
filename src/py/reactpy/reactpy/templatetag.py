from jinja2_simple_tags import StandaloneTag
from uuid import uuid4
import urllib.parse

REACTPY_WEBSOCKET_URL: str
REACTPY_WEB_MODULES_URL: str
REACTPY_RECONNECT_MAX: str
REACTPY_CLIENT_URL_PATH: str

class ComponentTag(StandaloneTag):
    safe_output = True
    tags = {"component"}

    def render(self, dotted_path: str, *args, **kwargs):
        uuid = uuid4().hex
        class_ = kwargs.pop("class", "")
        kwargs.pop("key", "")  # `key` is effectively useless for the root node
        url_path = REACTPY_CLIENT_URL_PATH
        if kwargs.get("args") is not None:
            raise ValueError("Cannot specify `args` as a keyword argument")
        if args:
            kwargs["args"] = args
        if kwargs:
            url_path += f"?{urllib.parse.urlencode(kwargs)}"

        return (
            f'<div id="{ uuid }" class="{ class_ }"></div>'
            '<script type="module" crossorigin="anonymous">'
            f'import {{ mountViewToElement }} from "{url_path}";'
            f'const mountElement = document.getElementById("{ uuid }");'
            "mountViewToElement("
            "    mountElement,"
            f'   "{ REACTPY_WEBSOCKET_URL }",'
            f'   "{ REACTPY_WEB_MODULES_URL }",'
            f'   "{ REACTPY_RECONNECT_MAX }",'
            f'   "{ dotted_path }",'
            ");"
            "</script>"
        )
