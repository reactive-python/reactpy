from reactpy import component, html, use_state


# start
@component
def toolbar():
    messages, set_messages = use_state([])

    async def handle_toolbar_click(event):
        set_messages([*messages, "You clicked on the toolbar!"])

    async def handle_play_click(event):
        set_messages([*messages, "Playing!"])

    return html.div(
        {"className": "Toolbar", "onClick": handle_toolbar_click},
        html.button({"onClick": handle_play_click}, "Play Movie"),
    )
