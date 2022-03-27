# :lines: 11-

from idom import run
from idom.server import sanic as sanic_server


# the run() function is the entry point for examples
sanic_server.configure = lambda _, cmpt: run(cmpt)


from sanic import Sanic

from idom import component, html
from idom.server.sanic import configure


@component
def HelloWorld():
    return html.h1("Hello, world!")


app = Sanic("MyApp")
configure(app, HelloWorld)


if __name__ == "__main__":
    app.run(port=8000)
