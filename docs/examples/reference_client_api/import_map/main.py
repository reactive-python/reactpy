# start

from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import FileResponse
from starlette.routing import Route

from reactpy import component, html, use_state
from reactpy.executors.asgi import ReactPyMiddleware


@component
def counter():
    count, set_count = use_state(0)

    async def increment(_event):
        set_count(count + 1)

    return html.div(
        html.h1(f"count is {count}"),
        html.button({"onClick": increment}, "Add"),
    )


async def home(request):
    return FileResponse(Path(__file__).parent / "page.html")


my_app = ReactPyMiddleware(
    Starlette(routes=[Route("/", home)]),
    root_components=["main.counter"],
)
