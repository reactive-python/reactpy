# :lines: 11-

from reactpy import run
from reactpy.backend import starlette as starlette_server


# the run() function is the entry point for examples
starlette_server.configure = lambda _, cmpt: run(cmpt)


from starlette.applications import Starlette

from reactpy import component, html
from reactpy.backend.starlette import configure


@component
def HelloWorld():
    return html.h1("Hello, world!")


app = Starlette()
configure(app, HelloWorld)
