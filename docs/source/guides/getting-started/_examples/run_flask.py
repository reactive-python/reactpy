# :lines: 11-

from reactpy import run
from reactpy.backend import flask as flask_server

# the run() function is the entry point for examples
flask_server.configure = lambda _, cmpt: run(cmpt)


from flask import Flask

from reactpy import component, html
from reactpy.backend.flask import configure


@component
def HelloWorld():
    return html.h1("Hello, world!")


app = Flask(__name__)
configure(app, HelloWorld)
