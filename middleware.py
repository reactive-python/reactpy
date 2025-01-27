from starlette.applications import Starlette
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from reactpy import component, hooks, html
from reactpy.backend.middleware import ReactPyMiddleware

templates = Jinja2Templates(
    directory="templates", extensions=["reactpy.jinja.ReactPyTemplateTag"]
)


@component
def Counter():
    count, set_count = hooks.use_state(0)

    def increment(event):
        set_count(count + 1)

    return html.div(
        html.button({"onClick": increment}, "Increment"),
        html.p(f"Count: {count}"),
    )


async def homepage(request):
    return templates.TemplateResponse(request, "index.html")


app = Starlette(
    debug=True,
    routes=[
        Route("/", homepage),
    ],
)

app = ReactPyMiddleware(app, ["middleware.Counter"])
