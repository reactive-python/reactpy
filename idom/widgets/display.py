import uuid
import json
from typing import Any, Optional, Dict
from urllib.parse import urlparse, urlencode


def display(kind: str, *args: Any, **kwargs: Any) -> Any:
    """Display an IDOM layout.

    Parameters:
        kind: how output should be displayed.
        args: Positional arguments passed to the output method.
        kwargs: Keyword arguments passed to the output method.
    """
    wtype = {"jupyter": JupyterWigdet}[kind]
    return wtype(*args, **kwargs)


class JupyterWigdet:
    """Output for IDOM within a Jupyter Notebook."""

    __slots__ = ("location", "path", "query")

    def __init__(self, url: str, query: Optional[Dict[str, Any]] = None) -> None:
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            self.location = "window.location"
        else:
            self.location = json.dumps(
                {"host": parsed_url.netloc, "protocol": parsed_url.scheme + ":"}
            )
        self.path = parsed_url.path
        self.query = urlencode(query or {})

    def _script(self, mount_id):
        return f"""
        <script type="module">
            const loc = {self.location};
            const idom_url = "//" + loc.host + "{self.path}";
            const http_proto = loc.protocol;
            const ws_proto = (http_proto === "https:") ? "wss:" : "ws:";
            // we want to avoid making this request (in case of CORS)
            // unless we know an IDOM server is expected to respond
            fetch(http_proto + idom_url, {{mode: "no-cors"}}).then(rsp => {{
                import(http_proto + idom_url + "/client/core_modules/layout.js").then(
                    (module) => {{
                        module.renderLayout(
                            document.getElementById("{mount_id}"),
                            ws_proto + idom_url + "/stream?{self.query}"
                        );
                    }}
                );
            }});
        </script>
        """

    def _repr_html_(self) -> str:
        """Rich HTML display output."""
        mount_id = "idom-" + uuid.uuid4().hex
        return f"""
        <div id="{mount_id}" class="idom-widget"/>
        {self._script(mount_id)}
        """

    def __repr__(self) -> str:
        return "%s(%r)" % (type(self).__name__, self.path)
