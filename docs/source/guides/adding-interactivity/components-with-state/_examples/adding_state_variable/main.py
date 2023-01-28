import json
from pathlib import Path

from idom import component, hooks, html, run


HERE = Path(__file__)
DATA_PATH = HERE.parent / "data.json"
sculpture_data = json.loads(DATA_PATH.read_text())


@component
def Gallery():
    index, set_index = hooks.use_state(0)

    def handle_click(event):
        set_index(index + 1)

    bounded_index = index % len(sculpture_data)
    sculpture = sculpture_data[bounded_index]
    alt = sculpture["alt"]
    artist = sculpture["artist"]
    description = sculpture["description"]
    name = sculpture["name"]
    url = sculpture["url"]

    return html.div(
        html.button("Next", on_click=handle_click),
        html.h2(name, " by ", artist),
        html.p(f"({bounded_index + 1} of {len(sculpture_data)})"),
        html.img(src=url, alt=alt, style={"height": "200px"}),
        html.p(description),
    )


run(Gallery)
