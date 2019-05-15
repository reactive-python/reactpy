import os
import uuid

from typing import Any

from idom.core import STATIC_DIRECTORY


def display(kind: str, *args: Any, **kwargs: Any) -> Any:
    """Display an iDOM layout.

    Parameters:
        kind: how output should be displayed.
        args: Positional arguments passed to the output method.
        kwargs: Keyword arguments passed to the output method.
    """
    wtype = {"jupyter": JupyterWigdet}[kind]
    return wtype(*args, **kwargs)


class JupyterWigdet:
    """Output for iDOM within a Jupyter Notebook."""

    _shown = False
    __slots__ = "_url"

    def __init__(self, url: str) -> None:
        self._url = url

    def _script(self) -> str:
        JS = os.path.join(STATIC_DIRECTORY, "jupyter-widget", "static", "js")
        for filename in os.listdir(JS):
            if os.path.splitext(filename)[1] == ".js":
                with open(os.path.join(JS, filename), "r") as f:
                    return f.read()
        else:
            raise ValueError("Failed to find script.")

    def _repr_html_(self) -> str:
        """Rich HTML display output."""
        mount_id = uuid.uuid4().hex
        return f"""
        <div id="{mount_id}"/>
        {'' if JupyterWigdet._shown else '<script>' + self._script() + '</script>'}
        <script>window.iDomWidgetMount("{self._url}", "{mount_id}")</script>
        """

    def __repr__(self) -> str:
        return "%s(%r)" % (type(self).__name__, self._url)
