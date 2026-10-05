import asyncio

from reactpy import component, html, use_state


# start
@component
def counter():
    number, set_number = use_state(0)
    seen, set_seen = use_state([])

    def handle_click(event):
        set_number(number + 5)

        def delayed():
            # Runs long after this render, but still sees this render's value.
            set_seen([*seen, number])

        asyncio.get_running_loop().call_later(3, delayed)

    return html.div(
        html.h1(number),
        html.button({"onClick": handle_click}, "+5"),
        html.p("Handler saw (3s later): ", ", ".join(map(str, seen)) or "-"),
    )
