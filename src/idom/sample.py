from __future__ import annotations

from . import html
from .core.component import component
from .core.types import VdomDict


@component
def SampleApp() -> VdomDict:
    return html.div(
        html.h1("Sample Application"),
        html.p(
            "This is a basic application made with IDOM. Click ",
            html.a("here", href="https://pypi.org/project/idom/", target="_blank"),
            " to learn more.",
        ),
        id="sample",
        style={"padding": "15px"},
    )
