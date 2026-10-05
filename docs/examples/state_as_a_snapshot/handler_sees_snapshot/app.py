from reactpy import component, html, use_state


# start
@component
def counter():
    number, set_number = use_state(0)
    seen, set_seen = use_state([])

    def handle_click(event):
        set_number(number + 5)
        # `number` here is still the value from THIS render.
        set_seen([*seen, number])

    return html.div(
        html.h1(number),
        html.button({"onClick": handle_click}, "+5"),
        html.p("Handler saw: ", ", ".join(map(str, seen)) or "-"),
    )
