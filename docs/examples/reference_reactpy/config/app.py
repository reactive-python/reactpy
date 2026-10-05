from reactpy import component, html
from reactpy.executors.asgi import ReactPy


@component
def page():
    return html.div(html.h1("Hello"), html.p("Welcome to the app."))


# start
my_app = ReactPy(
    page,
    path_prefix="/apps/reactpy/",
    reconnect_interval=500,
    reconnect_max_interval=30000,
    reconnect_max_retries=50,
    async_rendering=True,
    debug=False,
)
