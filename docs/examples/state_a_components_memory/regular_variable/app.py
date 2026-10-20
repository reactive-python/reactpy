from data import sculptures

from reactpy import component, html


# start
@component
def gallery():
    index = 0

    async def handle_next(event):
        # `nonlocal` is what makes this assignment legal Python at all; without
        # it the nested function gets its own `index` and the read on the right
        # hand side raises UnboundLocalError. JS closures need no such keyword.
        nonlocal index
        index = index + 1

    sculpture = sculptures[index]
    return html.div(
        html.button({"onClick": handle_next}, "Next"),
        html.h2(html.i(sculpture["name"]), " by ", sculpture["artist"]),
        html.h3(f"({index + 1} of {len(sculptures)})"),
        html.img({"src": sculpture["url"], "alt": sculpture["alt"]}),
        html.p(sculpture["description"]),
    )
