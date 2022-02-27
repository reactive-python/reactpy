from sanic import Sanic
from sanic.response import file

from idom import component, html
from idom.server.sanic import Config, PerClientStateServer


app = Sanic(__name__)


@app.route("/")
async def index(request):
    return await file("index.html")


@component
def IdomView():
    return html.code("This text came from an IDOM App")


PerClientStateServer(IdomView, app=app, config=Config(url_prefix="/_idom"))

app.run(host="127.0.0.1", port=5000)
