from __future__ import annotations

import webbrowser
from typing import Any

from idom.server.proto import ServerType

from . import html
from .core.component import component
from .core.proto import VdomDict
from .server.utils import find_available_port, find_builtin_server_type


@component
def App() -> VdomDict:
    return html.div(
        {"style": {"padding": "15px"}},
        html.h1("Sample Application"),
        html.p(
            "This is a basic application made with IDOM. Click ",
            html.a(
                {"href": "https://pypi.org/project/idom/", "target": "_blank"},
                "here",
            ),
            " to learn more.",
        ),
    )


def run_sample_app(
    host: str = "127.0.0.1",
    port: int | None = None,
    open_browser: bool = False,
    run_in_thread: bool | None = None,
) -> ServerType[Any]:
    """Run a sample application.

    Args:
        host: host where the server should run
        port: the port on the host to serve from
        open_browser: whether to open a browser window after starting the server
    """
    port = port or find_available_port(host)
    server_type = find_builtin_server_type("PerClientStateServer")
    server = server_type(App)

    run_in_thread = open_browser or run_in_thread

    if not run_in_thread:  # pragma: no cover
        server.run(host=host, port=port)
        return server

    thread = server.run_in_thread(host=host, port=port)
    server.wait_until_started(5)

    if open_browser:  # pragma: no cover
        webbrowser.open(f"http://{host}:{port}")
        thread.join()

    return server
