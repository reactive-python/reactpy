import os
import sys
from pathlib import Path

from sanic import Sanic, response

import idom
from idom.server.sanic import PerClientStateServer
from idom.widgets.utils import multiview

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
        idom.run = mount[file.stem]

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


PerClientStateServer(component, {"redirect_root_to_index": False}).register(app)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        workers=int(os.environ.get("WEB_CONCURRENCY", 1)),
        debug=bool(int(os.environ.get("DEBUG", "0"))),
    )
