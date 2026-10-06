from jinja2 import Environment, FileSystemLoader
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from reactpy import component, html, use_state
from reactpy.executors.asgi import ReactPyMiddleware
from reactpy.templatetags import ReactPyJinja


@component
def counter():
    count, set_count = use_state(0)
    return html.div(
        html.h1(count),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Add 1"),
    )


# start
templates = Jinja2Templates(
    env=Environment(
        loader=FileSystemLoader("templates"),
        extensions=[ReactPyJinja],
        autoescape=True,
    )
)


async def home(request):
    return templates.TemplateResponse(request, "home.html")


starlette_app = Starlette(routes=[Route("/", home)])

# The dotted path must be importable by the server: the browser asks ReactPy to
# render `pages.counter`, and that lookup happens on the server, not in the
# template. Register the same path here that the template passes to the tag.
my_app = ReactPyMiddleware(starlette_app, root_components=["main.counter"])
