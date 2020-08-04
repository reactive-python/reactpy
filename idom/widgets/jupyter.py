from idom.core.element import ElementConstructor
import uuid
import json
import os
from weakref import finalize
from typing import Any, Optional, Any, Optional, Dict, Callable
from urllib.parse import urlparse, urlencode

from idom.server import find_available_port, multiview_server
from idom.server.sanic import PerClientStateServer


def init_display(
    host: str,
    server_options: Optional[Any] = None,
    run_options: Optional[Dict[str, Any]] = None,
) -> Callable[..., "JupyterDisplay"]:
    """Initialize an IDOM server and return a function for displaying IDOM in Jupyter

    .. note::

        If running on JupyterHub we attempt to infer the URL of the initialized server
        using `available environment variables <jupyterhub-envvars>`_. For this to work
        though we assume the presence of a ``jupyter_server_proxy`` (see
        `here <jupyter-server-proxy>`_ for more info on the proxy).

    .. jupyterhub-envvars: https://github.com/jupyterhub/jupyterhub/blob/e5a6119505f89a293447ce4e727c4bd15e86b145/docs/source/reference/services.md#launching-a-hub-managedservice
    .. jupyter-server-proxy: https://github.com/jupyterhub/jupyter-server-proxy
    """
    host, port = "127.0.0.1", find_available_port(host)
    server_options = server_options or {"cors": True}
    run_options = run_options or {"access_log": False}
    multiview_mount, _ = multiview_server(
        PerClientStateServer, host, port, server_options, run_options
    )

    if "JUPYTERHUB_SERVICE_PREFIX" in os.environ:
        # Use this if we're running on a Jupyter instance managed by JupyterHub
        server_url = f"{os.environ['JUPYTERHUB_SERVICE_PREFIX']}/proxy/{port}"
    else:
        # Otherwise assume we're running locally (this might not be correct though...)
        server_url = f"http://{host}:{port}"

    def display(
        element: ElementConstructor, *args: Any, **kwargs: Any
    ) -> JupyterDisplay:
        view_id = multiview_mount(element, *args, **kwargs)
        widget = JupyterDisplay(server_url, {"view_id": view_id})
        finalize(widget, multiview_mount.remove, view_id)
        return widget

    return display


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
