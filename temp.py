from flask import Flask

import idom
from idom.server import flask as server


app = Flask(__name__)


@idom.component
def HelloWorld():
    print(server.use_scope())
    return idom.html.h1("Hello, world!")


idom.run(HelloWorld, implementation=server)

# server.configure(app, HelloWorld)
