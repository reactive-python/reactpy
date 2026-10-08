from data import sculptures

from reactpy import component, html, use_state


# start
@component
def gallery():
    index, set_index = use_state(0)
    show_more, set_show_more = use_state(False)

    def handle_next(event):
        set_index(index + 1)

    def handle_more(event):
        set_show_more(not show_more)

    sculpture = sculptures[index]
    return html.div(
        html.button({"onClick": handle_next}, "Next"),
        html.h2(html.i(sculpture["name"]), " by ", sculpture["artist"]),
        html.h3(f"({index + 1} of {len(sculptures)})"),
        html.button(
            {"onClick": handle_more}, "Hide details" if show_more else "Show details"
        ),
        html.p(sculpture["description"]) if show_more else None,
        html.img({"src": sculpture["url"], "alt": sculpture["alt"]}),
    )
