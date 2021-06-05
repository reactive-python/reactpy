import os
import sys
from functools import partial
from pathlib import Path

from sanic import Sanic, response

import idom
from idom.client.manage import web_modules_dir
from idom.server.sanic import PerClientStateServer
from idom.widgets.utils import multiview


HERE = Path(__file__).parent
IDOM_MODEL_SERVER_URL_PREFIX = "/_idom"


def make_app():
    app = Sanic(__name__)
    app.static("/docs", str(HERE / "build"))
    app.static("/_modules", str(web_modules_dir()))

    @app.route("/")
    async def forward_to_index(request):
        return response.redirect("/docs/index.html")

    return app


def make_component():
    mount, component = multiview()

    examples_dir = HERE / "source" / "examples"
    sys.path.insert(0, str(examples_dir))

    original_run = idom.run
    try:
        for file in examples_dir.iterdir():
            if (
                not file.is_file()
                or not file.suffix == ".py"
                or file.stem.startswith("_")
            ):
                continue

            # Modify the run function so when we exec the file
            # instead of running a server we mount the view.
            idom.run = partial(mount.add, file.stem)

            with file.open() as f:
                try:
                    exec(
                        f.read(),
                        {
                            "__file__": str(file),
                            "__name__": f"__main__.examples.{file.stem}",
                        },
                    )
                except Exception as error:
                    raise RuntimeError(f"Failed to execute {file}") from error
    finally:
        idom.run = original_run

    return component


if __name__ == "__main__":
    app = make_app()

    PerClientStateServer(
        make_component(),
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
