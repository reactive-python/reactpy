from reactpy import component, html
from reactpy.backend.flask import configure
from flask import Flask


@component
def TestComponent():
    return html.h1("Hello, world!!!")


app = Flask(__name__)
configure(app, TestComponent)