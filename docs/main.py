import os
import sys
from pathlib import Path
from pathlib import Path

from sanic import Sanic
from sanic import response

from idom.widgets.utils import multiview
from idom.client.manage import STATIC_DIR
from idom.server.sanic import PerClientStateServer

app = Sanic(__name__)
app.static("/docs", "./docs/build")
app.static("/favicon.ico", str(STATIC_DIR / "favicon.ico"))


@app.route("/")
async def forward_to_index(request):
    return response.redirect("/docs/index.html")


mount, element = multiview()

here = Path(__file__).parent
widgets = here / "source" / "widgets"
sys.path.insert(0, str(widgets))

for file in widgets.iterdir():
    if not file.is_file() or not file.suffix == ".py" or file.stem.startswith("_"):
        continue

    with file.open() as f:
        exec(
            f.read(),
            {
                "display": getattr(mount, file.stem),
                "__file__": str(file),
                "__name__": f"widgets.{file.stem}",
            },
        )

PerClientStateServer(element).configure({"redirect_root_to_index": False}).register(app)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        workers=int(os.environ.get("WEB_CONCURRENCY", 1)),
    )
