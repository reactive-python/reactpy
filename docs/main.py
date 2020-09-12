import os
import sys
from pathlib import Path
from pathlib import Path

from sanic import Sanic
from sanic import response

from idom.widgets.utils import multiview
from idom.client.manage import APP_DIR
from idom.server.sanic import PerClientStateServer

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

for file in examples_dir.iterdir():
    if not file.is_file() or not file.suffix == ".py" or file.stem.startswith("_"):
        continue

    with file.open() as f:
        exec(
            f.read(),
            {
                "display": mount[file.stem],
                "__file__": str(file),
                "__name__": f"widgets.{file.stem}",
            },
        )

server = (
    PerClientStateServer(element)
    .configure({"redirect_root_to_index": False})
    .register(app)
)


def prod():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        workers=int(os.environ.get("WEB_CONCURRENCY", 1)),
        debug={"true": True, "false": False}[os.environ.get("DEBUG", "False").lower()],
    )


def local():
    import webbrowser

    thread = server.daemon("127.0.0.1", 5000)
    webbrowser.open("http://127.0.0.1:5000/")
    thread.join()


if __name__ == "__main__":
    prod()
