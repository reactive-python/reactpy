from jinja2 import Environment, FileSystemLoader
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from reactpy.templatetags import ReactPyJinja

jinja_templates = Jinja2Templates(
    env=Environment(
        loader=FileSystemLoader("path/to/my_templates"),
        extensions=[ReactPyJinja],
    )
)


async def example_webpage(request):
    return jinja_templates.TemplateResponse(request, "my_template.html")


starlette_app = Starlette(routes=[Route("/", example_webpage)])
