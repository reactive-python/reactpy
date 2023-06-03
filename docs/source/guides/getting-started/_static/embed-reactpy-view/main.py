from sanic import Sanic
from sanic.response import file

from reactpy import component, html
from reactpy.backend.sanic import Options, configure

app = Sanic("MyApp")


@app.route("/")
async def index(request):
    return await file("index.html")


@component
def ReactPyView():
    return html.code("This text came from an ReactPy App")


configure(app, ReactPyView, Options(url_prefix="/_reactpy"))

app.run(host="127.0.0.1", port=5000)
