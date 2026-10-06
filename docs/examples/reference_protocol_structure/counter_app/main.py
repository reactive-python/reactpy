# start

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from reactpy import component, html, use_state
from reactpy.executors.asgi import ReactPyMiddleware
from reactpy.executors.utils import server_side_component_html


@component
def counter():
    count, set_count = use_state(0)

    def increment(_event):
        set_count(count + 1)

    return html.div(
        html.h1(f"count is {count}"),
        html.button({"onClick": increment}, "Add"),
    )


async def home(request):
    return HTMLResponse(
        "<!doctype html>"
        "<html><body>"
        + server_side_component_html("root", "", "main.counter/")
        + "</body></html>"
    )


my_app = ReactPyMiddleware(
    Starlette(routes=[Route("/", home)]),
    root_components=["main.counter"],
)
