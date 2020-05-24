from pathlib import Path
import sys
from pathlib import Path

from sanic import Sanic

from idom.widgets.utils import multiview
from idom.server.sanic import PerClientStateServer

app = Sanic(__name__)
app.static("/docs", "./docs/build")

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

PerClientStateServer(element).configure({}).register(app)

app.run("0.0.0.0", 80)
