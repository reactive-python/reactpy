import os
from logging import getLogger
from pathlib import Path

from sanic import Sanic, response

from idom.server.sanic import PerClientStateServer
from idom.widgets import multiview

from .examples import load_examples


HERE = Path(__file__).parent
IDOM_MODEL_SERVER_URL_PREFIX = "/_idom"

logger = getLogger(__name__)


IDOM_MODEL_SERVER_URL_PREFIX = "/_idom"


def run():
    app = make_app()

    PerClientStateServer(
        make_examples_component(),
        {
            "redirect_root_to_index": False,
            "url_prefix": IDOM_MODEL_SERVER_URL_PREFIX,
        },
        app,
    )

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        workers=int(os.environ.get("WEB_CONCURRENCY", 1)),
        debug=bool(int(os.environ.get("DEBUG", "0"))),
    )


def make_app():
    app = Sanic(__name__)

    app.static("/docs", str(HERE / "build"))

    @app.route("/")
    async def forward_to_index(request):
        return response.redirect("/docs/index.html")

    return app


def make_examples_component():
    mount, component = multiview()

    for example_name, example_component in load_examples():
        mount.add(example_name, example_component)

    return component
