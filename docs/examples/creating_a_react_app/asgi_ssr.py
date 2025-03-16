from reactpy import component, html
from reactpy.executors.asgi import ReactPy


@component
def hello_world():
    return html.div("Hello World")


my_app = ReactPy(hello_world)
