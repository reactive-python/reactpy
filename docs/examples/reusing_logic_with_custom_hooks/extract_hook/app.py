"""A plain function that calls hooks is a custom Hook: it shares the logic, and
each component that calls it gets its own state.
"""

from reactpy import component, html, use_state


# start
def use_cart(items):
    """Selection logic for a list of items — the state lives in the caller."""
    selected, set_selected = use_state([])

    def handler_for(item):
        def toggle(event):
            if item in selected:
                set_selected([name for name in selected if name != item])
            else:
                set_selected([*selected, item])

        return toggle

    return selected, handler_for


@component
def checkout(items):
    selected, handler_for = use_cart(items)
    total = 10 * len(selected)
    return html.div(
        html.ul(
            [
                html.li(
                    {"key": item},
                    html.button(
                        {"onClick": handler_for(item)},
                        f"{item} {'[x]' if item in selected else '[ ]'}",
                    ),
                )
                for item in items
            ]
        ),
        html.p(f"{len(selected)} selected, total ${total}"),
    )


@component
def app():
    return checkout(["apple", "bread", "cheese"])
