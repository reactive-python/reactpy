from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from reactpy import component, html, use_state
from reactpy.executors.asgi import ReactPyMiddleware
from reactpy.executors.utils import server_side_component_html


@component
def counter():
    count, set_count = use_state(0)

    async def handle_count_click(event):
        set_count(count + 1)

    return html.div(
        html.h1(count),
        html.button({"onClick": handle_count_click}, "Add 1"),
    )


# start
async def home(request):
    # The mount point plus the client bootstrap, for one registered component.
    mount = server_side_component_html(
        element_id="app",
        class_="",
        # Trailing slash required: the websocket route matches `<prefix><dotted_path>/`.
        component_path="main.counter/",
    )
    return HTMLResponse(f'<html><body><div id="wrapper">{mount}</div></body></html>')


starlette_app = Starlette(routes=[Route("/", home)])

my_app = ReactPyMiddleware(starlette_app, root_components=["main.counter"])
