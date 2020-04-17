import uuid
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from IPython import display as _ipy_display


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

    _idom_server_exists_displayed = False
    __slots__ = ("_ws", "_http")

    def __init__(self, url: str, secure=True) -> None:
        uri = urlunsplit(("",) + urlsplit(url)[1:])
        if uri.endswith("/"):
            uri = uri[:-1]
        if secure:
            ws_proto = "wss"
            http_proto = "https"
        else:
            ws_proto = "ws"
            http_proto = "http"
        self._ws = ws_proto + ":" + uri
        self._http = http_proto + ":" + uri
        if not type(self)._idom_server_exists_displayed:
            _ipy_display.display_html(
                "<script>document.idomServerExists = true;</script>", raw=True,
            )
            _ipy_display.clear_output(wait=True)
            type(self)._idom_server_exists_displayed = True

    def _script(self, mount_id):
        return f"""
        <script type="module">
            // we want to avoid making this request (in case of CORS)
            // unless we know an IDOM server is expected to respond
            if (document.idomServerExists) {{
                import("{self._http}/client/core_modules/layout.js").then(
                    module => {{
                        module.renderLayout(
                            document.getElementById("{mount_id}"), "{self._ws}/stream"
                        )
                    }}
                )
            }}
        </script>
        """

    def _repr_html_(self) -> str:
        """Rich HTML display output."""
        mount_id = uuid.uuid4().hex
        return f"""
        <div id="{mount_id}"/>
        {self._script(mount_id)}
        """

    def __repr__(self) -> str:
        return "%s(%r)" % (type(self).__name__, self._http)
