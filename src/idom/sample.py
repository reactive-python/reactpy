from __future__ import annotations

from . import html
from .core.component import component
from .core.types import VdomDict


@component
def SampleApp() -> VdomDict:
    return html.div(
        {"id": "sample", "style": {"padding": "15px"}},
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
