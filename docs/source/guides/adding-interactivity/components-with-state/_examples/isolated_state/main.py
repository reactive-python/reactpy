import json
from pathlib import Path

from reactpy import component, hooks, html, run


HERE = Path(__file__)
DATA_PATH = HERE.parent / "data.json"
sculpture_data = json.loads(DATA_PATH.read_text())


@component
def Gallery():
    index, set_index = hooks.use_state(0)
    show_more, set_show_more = hooks.use_state(False)

    def handle_next_click(event):
        set_index(index + 1)

    def handle_more_click(event):
        set_show_more(not show_more)

    bounded_index = index % len(sculpture_data)
    sculpture = sculpture_data[bounded_index]
    alt = sculpture["alt"]
    artist = sculpture["artist"]
    description = sculpture["description"]
    name = sculpture["name"]
    url = sculpture["url"]

    return html.div(
        html.button({"on_click": handle_next_click}, "Next"),
        html.h2(name, " by ", artist),
        html.p(f"({bounded_index + 1} or {len(sculpture_data)})"),
        html.img({"src": url, "alt": alt, "style": {"height": "200px"}}),
        html.div(
            html.button(
                {"on_click": handle_more_click},
                f"{('Show' if show_more else 'Hide')} details",
            ),
            (html.p(description) if show_more else ""),
        ),
    )


@component
def App():
    return html.div(
        html.section({"style": {"width": "50%", "float": "left"}}, Gallery()),
        html.section({"style": {"width": "50%", "float": "left"}}, Gallery()),
    )


run(App)
