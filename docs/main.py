import os
import sys
from pathlib import Path
from pathlib import Path

from sanic import Sanic
from sanic import response

import idom
from idom.widgets.utils import multiview
from idom.client.manage import APP_DIR
from idom.server.sanic import PerClientStateServer

idom_build_config = {
    "js_dependencies": [
        "@material-ui/core",
        "victory",
        "semantic-ui-react",
        "jquery",
    ]
}

here = Path(__file__).parent

app = Sanic(__name__)
app.static("/docs", str(here / "build"))
app.static("/favicon.ico", str(APP_DIR / "favicon.ico"))


@app.route("/")
async def forward_to_index(request):
    return response.redirect("/docs/index.html")


mount, element = multiview()

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


server = PerClientStateServer(element, {"redirect_root_to_index": False}).register(app)


def prod():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        workers=int(os.environ.get("WEB_CONCURRENCY", 1)),
        debug={"true": True, "false": False}[os.environ.get("DEBUG", "False").lower()],
    )


def local(path=""):
    import webbrowser

    thread = server.daemon("127.0.0.1", 5000)
    path = f"docs/{path}" if path else ""
    webbrowser.open(f"http://127.0.0.1:5000/{path}")
    thread.join()


if __name__ == "__main__":
    prod()
