# :lines: 11-

from reactpy import run
from reactpy.backend import fastapi as fastapi_server


# the run() function is the entry point for examples
fastapi_server.configure = lambda _, cmpt: run(cmpt)


from fastapi import FastAPI

from reactpy import component, html
from reactpy.backend.fastapi import configure


@component
def HelloWorld():
    return html.h1("Hello, world!")


app = FastAPI()
configure(app, HelloWorld)
