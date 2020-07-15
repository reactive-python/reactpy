import uuid
import json
import os
from weakref import finalize
from typing import Any, Optional, Any, Optional, Dict, Callable
from urllib.parse import urlparse, urlencode

import idom
from idom.server import find_available_port, multiview_server
from idom.server.sanic import PerClientStateServer


def init_display(
    host: str,
    server_options: Optional[Any] = None,
    run_options: Optional[Dict[str, Any]] = None,
) -> Callable[..., "JupyterDisplay"]:
    host, port = "127.0.0.1", find_available_port(host)
    server_options = server_options or {"cors": True}
    run_options = run_options or {"access_log": False}
    multiview_mount, _ = multiview_server(
        PerClientStateServer, host, port, server_options, run_options
    )
    server_url = _find_server_url(host, port)

    def display(element, *args, **kwargs):
        view_id = multiview_mount(element, *args, **kwargs)
        widget = idom.JupyterDisplay(server_url, {"view_id": view_id})
        finalize(widget, multiview_mount.remove, view_id)
        return widget

    return display


def _find_server_url(host: str, port: int) -> str:
    localhost_idom_path = f"http://{host}:{port}"
    jupyterhub_idom_path = _path_to_jupyterhub_proxy(port)
    return jupyterhub_idom_path or localhost_idom_path


def _path_to_jupyterhub_proxy(port: int) -> Optional[str]:
    """If running on Jupyterhub return the path from the host's root to a proxy server

    This is used when examples are running on mybinder.org or in a container created by
    jupyter-repo2docker. For this to work a ``jupyter_server_proxy`` must have been
    instantiated. See https://github.com/jupyterhub/jupyter-server-proxy
    """
    if "JUPYTERHUB_OAUTH_CALLBACK_URL" in os.environ:
        url = os.environ["JUPYTERHUB_OAUTH_CALLBACK_URL"].rsplit("/", 1)[0]
        return f"{url}/proxy/{port}"
    elif "JUPYTER_SERVER_URL" in os.environ:
        return f"{os.environ['JUPYTER_SERVER_URL']}/proxy/{port}"
    else:
        return None


class JupyterDisplay:
    """Output for IDOM within a Jupyter Notebook."""

    __slots__ = ("location", "path", "query", "__weakref__")

    def __init__(self, url: str = "", query: Optional[Dict[str, Any]] = None) -> None:
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            self.location = "window.location"
        else:
            self.location = json.dumps(
                {"host": parsed_url.netloc, "protocol": parsed_url.scheme + ":"}
            )
        self.path = parsed_url.path
        self.query = urlencode(query or {})

    def _script(self, mount_id: str) -> str:
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
        return f"{type(self).__name__}({self.location}, path={self.path!r})"
