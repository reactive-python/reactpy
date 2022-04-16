# :lines: 11-

from idom import run
from idom.backend import flask as flask_server


# the run() function is the entry point for examples
flask_server.configure = lambda _, cmpt: run(cmpt)


from flask import Flask

from idom import component, html
from idom.backend.flask import configure


@component
def HelloWorld():
    return html.h1("Hello, world!")


app = Flask(__name__)
configure(app, HelloWorld)
