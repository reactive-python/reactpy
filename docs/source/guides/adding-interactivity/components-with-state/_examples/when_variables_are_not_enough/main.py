# flake8: noqa
# errors F841,F823 for `index = index + 1` inside the closure

# :lines: 7-
# :linenos:

import json
from pathlib import Path

from reactpy import component, html, run


HERE = Path(__file__)
DATA_PATH = HERE.parent / "data.json"
sculpture_data = json.loads(DATA_PATH.read_text())


@component
def Gallery():
    index = 0

    def handle_click(event):
        index = index + 1

    bounded_index = index % len(sculpture_data)
    sculpture = sculpture_data[bounded_index]
    alt = sculpture["alt"]
    artist = sculpture["artist"]
    description = sculpture["description"]
    name = sculpture["name"]
    url = sculpture["url"]

    return html.div(
        html.button({"on_click": handle_click}, "Next"),
        html.h2(name, " by ", artist),
        html.p(f"({bounded_index + 1} or {len(sculpture_data)})"),
        html.img({"src": url, "alt": alt, "style": {"height": "200px"}}),
        html.p(description),
    )


run(Gallery)
