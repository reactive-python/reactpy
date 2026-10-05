from reactpy import component, html, use_state


# start
@component
def counter():
    number, set_number = use_state(0)

    def handle_click(event):
        # number is 0 for this render, so this reads as set_number(5).
        set_number(number + 5)
        set_number(lambda n: n + 1)

    return html.div(
        html.h1(number),
        html.button({"onClick": handle_click}, "Increase the number"),
    )
