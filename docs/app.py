import os
from logging import getLogger
from pathlib import Path

from sanic import Sanic, response

from idom import component
from idom.core.types import ComponentConstructor
from idom.server.sanic import Options, configure, use_request

from .examples import get_normalized_example_name, load_examples


HERE = Path(__file__).parent
IDOM_MODEL_SERVER_URL_PREFIX = "/_idom"

logger = getLogger(__name__)


IDOM_MODEL_SERVER_URL_PREFIX = "/_idom"


def run():
    app = make_app()

    configure(
        app,
        Example(),
        Options(url_prefix=IDOM_MODEL_SERVER_URL_PREFIX),
    )

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        workers=int(os.environ.get("WEB_CONCURRENCY", 1)),
        debug=bool(int(os.environ.get("DEBUG", "0"))),
    )


@component
def Example():
    raw_view_id = use_request().get_args().get("view_id")
    view_id = get_normalized_example_name(raw_view_id)
    return _get_examples()[view_id]()


def _get_examples():
    if not _EXAMPLES:
        _EXAMPLES.update(load_examples())
    return _EXAMPLES


def reload_examples():
    _EXAMPLES.clear()
    _EXAMPLES.update(load_examples())


_EXAMPLES: dict[str, ComponentConstructor] = {}


def make_app():
    app = Sanic("docs_app")

    app.static("/docs", str(HERE / "build"))

    @app.route("/")
    async def forward_to_index(request):
        return response.redirect("/docs/index.html")

    return app
