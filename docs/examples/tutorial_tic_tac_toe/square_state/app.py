from reactpy import component, html, use_state

# start
# None is what an unfilled square holds; ReactPy renders None as nothing.
EMPTY_SQUARE: str | None = None


@component
def square():
    value, set_value = use_state(EMPTY_SQUARE)

    async def handle_click(event):
        set_value("X")

    return html.button({"className": "square", "onClick": handle_click}, value)


@component
def board():
    return html.fragment(
        html.div(
            {"className": "board-row"},
            square(),
            square(),
            square(),
        ),
        html.div(
            {"className": "board-row"},
            square(),
            square(),
            square(),
        ),
        html.div(
            {"className": "board-row"},
            square(),
            square(),
            square(),
        ),
    )
