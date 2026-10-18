from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from reactpy import component, html, use_state
from reactpy.executors.asgi import ReactPyMiddleware


@component
def counter():
    count, set_count = use_state(0)

    async def handle_count_click(event):
        set_count(count + 1)

    return html.div(
        html.h1(count),
        html.button({"onClick": handle_count_click}, "Add 1"),
    )


async def health(request):
    return PlainTextResponse("ok")


starlette_app = Starlette(routes=[Route("/healthz", health)])

# start
my_app = ReactPyMiddleware(starlette_app, root_components=["main.counter"])
