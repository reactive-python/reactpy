# start

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from reactpy import component, html, use_state
from reactpy.executors.asgi import ReactPyMiddleware

PATH_PREFIX = "/reactpy/"


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
    # pathPrefix and the bundle's URL both have to agree with the server's,
    # so both are interpolated from one value rather than typed twice.
    return HTMLResponse(f"""<!doctype html>
        <html>
          <body>
            <div id="app"></div>
            <script type="module" crossorigin="anonymous">
              import {{ mountReactPy }} from "{PATH_PREFIX}static/index.js";

              mountReactPy({{
                mountElement: document.getElementById("app"),
                pathPrefix: "{PATH_PREFIX}",
                componentPath: "main.counter/",
              }});
            </script>
          </body>
        </html>""")


my_app = ReactPyMiddleware(
    Starlette(routes=[Route("/", home)]),
    root_components=["main.counter"],
)
