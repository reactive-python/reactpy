from reactpy import component, html, use_state


# start
@component
def counter():
    count, set_count = use_state(0)
    history, set_history = use_state([])

    def handle_add(event):
        # Read history through an updater: `history` in this closure is the
        # value from the render that created the handler, not the latest.
        set_history(lambda previous: [*previous, count])
        set_count(count + 1)

    return html.div(
        html.h1(count),
        html.button({"onClick": handle_add}, "Add 1"),
        html.p("Previous values: " + (", ".join(map(str, history)) or "-")),
    )
