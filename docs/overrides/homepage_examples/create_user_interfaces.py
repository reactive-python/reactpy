# ruff: noqa: INP001
from reactpy import component, html


def thumbnail(*_, **__): ...


def like_button(*_, **__): ...


@component
def video(data):
    return html.div(
        thumbnail(data),
        html.a(
            {"href": data.url},
            html.h3(data.title),
            html.p(data.description),
        ),
        like_button(data),
    )
