from data import sculptures

from reactpy import component, html, use_state


# start
@component
def gallery():
    index, set_index = use_state(0)

    async def handle_next(event):
        set_index(index + 1)

    sculpture = sculptures[index]
    return html.div(
        html.button({"onClick": handle_next}, "Next"),
        html.h2(html.i(sculpture["name"]), " by ", sculpture["artist"]),
        html.h3(f"({index + 1} of {len(sculptures)})"),
        html.img({"src": sculpture["url"], "alt": sculpture["alt"]}),
        html.p(sculpture["description"]),
    )
