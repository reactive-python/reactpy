import uuid

from typing import Any


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

    _shown = False
    __slots__ = "_url"
    _script = """
    import React from '{url}/web-modules/react.js';
    import ReactDOM from '{url}/web-modules/react-dom.js';
    import Layout from '{url}/js/idom-layout';

    function IdomWidgetMount(endpoint, mountId) {
        const mount = document.getElementById(mountId);
        const element = React.createElement(Layout, {{endpoint: endpoint}})
        ReactDOM.render(element, mount);
    };
    """

    def __init__(self, url: str) -> None:
        self._url = url

    def _repr_html_(self) -> str:
        """Rich HTML display output."""
        mount_id = uuid.uuid4().hex
        return f"""
        <div id="{mount_id}"/>
        {'' if JupyterWigdet._shown else '<script>' + self._script + '</script>'}
        <script>window.IdomWidgetMount("{self._url}", "{mount_id}")</script>
        """

    def __repr__(self) -> str:
        return "%s(%r)" % (type(self).__name__, self._url)
