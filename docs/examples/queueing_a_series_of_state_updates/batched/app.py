from reactpy import component, html, use_state


# start
@component
def counter():
    number, set_number = use_state(0)

    async def handle_click(event):
        set_number(number + 1)
        set_number(number + 1)
        set_number(number + 1)

    return html.div(
        html.h1(number),
        html.button({"onClick": handle_click}, "+3"),
    )
