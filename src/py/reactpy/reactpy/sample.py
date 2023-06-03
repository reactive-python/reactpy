from __future__ import annotations

from reactpy import html
from reactpy.core.component import component
from reactpy.core.types import VdomDict


@component
def SampleApp() -> VdomDict:
    return html.div(
        {"id": "sample", "style": {"padding": "15px"}},
        html.h1("Sample Application"),
        html.p(
            "This is a basic application made with ReactPy. Click ",
            html.a(
                {"href": "https://pypi.org/project/reactpy/", "target": "_blank"},
                "here",
            ),
            " to learn more.",
        ),
    )
