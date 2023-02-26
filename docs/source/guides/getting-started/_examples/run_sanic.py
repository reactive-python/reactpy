# :lines: 11-

from reactpy import run
from reactpy.backend import sanic as sanic_server


# the run() function is the entry point for examples
sanic_server.configure = lambda _, cmpt: run(cmpt)


from sanic import Sanic

from reactpy import component, html
from reactpy.backend.sanic import configure


@component
def HelloWorld():
    return html.h1("Hello, world!")


app = Sanic("MyApp")
configure(app, HelloWorld)


if __name__ == "__main__":
    app.run(port=8000)
