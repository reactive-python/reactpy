# :lines: 11-

from idom import run
from idom.server import fastapi as fastapi_server


# the run() function is the entry point for examples
fastapi_server.configure = lambda _, cmpt: run(cmpt)


from fastapi import FastAPI

from idom import component, html
from idom.server.fastapi import configure


@component
def HelloWorld():
    return html.h1("Hello, world!")


app = FastAPI()
configure(app, HelloWorld)
