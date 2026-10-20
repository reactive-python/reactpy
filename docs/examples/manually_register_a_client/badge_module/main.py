from pathlib import Path

from reactpy import component, html
from reactpy.reactjs import component_from_file

# start
HERE = Path(__file__).parent

Badge = component_from_file(
    HERE / "badge.js",
    "Badge",
    name="badge",
    fallback=html.p("loading badge..."),
)


@component
def product_card(title, tone):
    return html.div(
        html.h2(title),
        Badge({"label": "in stock", "tone": tone}, "ready to ship"),
    )


# end
