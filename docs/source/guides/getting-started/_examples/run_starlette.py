# :lines: 11-

from idom import run
from idom.backend import starlette as starlette_server


# the run() function is the entry point for examples
starlette_server.configure = lambda _, cmpt: run(cmpt)


from starlette.applications import Starlette

from idom import component, html
from idom.backend.starlette import configure


@component
def HelloWorld():
    return html.h1("Hello, world!")


app = Starlette()
configure(app, HelloWorld)
