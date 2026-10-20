from jinja2 import Environment, FileSystemLoader
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from reactpy.executors.asgi import ReactPyMiddleware
from reactpy.templatetags import ReactPyJinja

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

# The dotted path in the template is resolved on the server, not in the
# template: the browser asks ReactPy to render `pages.counter`, and ReactPy
# imports it to satisfy that request. Register exactly the paths the template
# passes to `{% component %}` -- here the `counter` and `badge` functions in
# the sibling `pages.py`.
my_app = ReactPyMiddleware(
    starlette_app, root_components=["pages.counter", "pages.badge"]
)
