from __future__ import annotations

import webbrowser
from typing import Any

from . import html
from .core.component import component
from .core.types import VdomDict
from .server.any import run


@component
def App() -> VdomDict:
    return html._(
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
) -> None:
    """Run a sample application.

    Args:
        host: host where the server should run
        port: the port on the host to serve from
        open_browser: whether to open a browser window after starting the server
    """
    run(App, host, port, open_browser=open_browser)
