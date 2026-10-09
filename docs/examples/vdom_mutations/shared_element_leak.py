from reactpy import component, html, use_state

# start
# Built once, at module scope. Every visitor's Layout renders this same dict.
STATUS = html.p({"id": "status"}, "idle")


@component
def panel():
    n, set_n = use_state(0)

    def mark_dirty(event):
        # Mutates the shared element and asks for no render: nothing changes
        # on screen, and the server's model now disagrees with every client.
        STATUS["children"] = [f"mutated by visitor {n}"]

    def bump(event):
        # The next render of ANY state in this component re-sends STATUS --
        # including the mutation, whoever made it.
        set_n(n + 1)

    return html.div(
        html.h1({"id": "counter"}, f"n={n}"),
        html.button({"id": "dirty", "onClick": mark_dirty}, "mutate"),
        html.button({"id": "bump", "onClick": bump}, "bump"),
        STATUS,
    )


# end
