import os
import sys
from functools import partial
from pathlib import Path

from sanic import Sanic, response

import idom
from idom.config import IDOM_CLIENT_IMPORT_SOURCE_URL
from idom.server.sanic import PerClientStateServer
from idom.widgets.utils import multiview


IDOM_MODEL_SERVER_URL_PREFIX = "/_idom"

IDOM_CLIENT_IMPORT_SOURCE_URL.set_default(
    # set_default because scripts/live_docs.py needs to overwrite this
    f"{IDOM_MODEL_SERVER_URL_PREFIX}{IDOM_CLIENT_IMPORT_SOURCE_URL.default}"
)


here = Path(__file__).parent

app = Sanic(__name__)
app.static("/docs", str(here / "build"))


@app.route("/")
async def forward_to_index(request):
    return response.redirect("/docs/index.html")


mount, component = multiview()

examples_dir = here / "source" / "examples"
sys.path.insert(0, str(examples_dir))


original_run = idom.run
try:
    for file in examples_dir.iterdir():
        if not file.is_file() or not file.suffix == ".py" or file.stem.startswith("_"):
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


PerClientStateServer(
    component,
    {
        "redirect_root_to_index": False,
        "url_prefix": IDOM_MODEL_SERVER_URL_PREFIX,
    },
).register(app)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        workers=int(os.environ.get("WEB_CONCURRENCY", 1)),
        debug=bool(int(os.environ.get("DEBUG", "0"))),
    )
