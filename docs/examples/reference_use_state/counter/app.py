from reactpy import component, html, use_state


# start
@component
def counter():
    step, set_step = use_state(1)

    async def handle_add(event):
        set_step(step + 1)

    return html.div(
        html.h1(step),
        html.button({"onClick": handle_add}, "Add 1"),
    )
