from reactpy import component, html, use_state


# start
@component
def button(on_click, *children):
    def handle_click(event):
        # Detected from this line, so the client stops the event before
        # it reaches the parent's handler.
        event.stopPropagation()
        on_click()

    return html.button({"onClick": handle_click}, *children)


@component
def toolbar():
    messages, set_messages = use_state([])

    def handle_toolbar_click(event):
        set_messages([*messages, "You clicked on the toolbar!"])

    def handle_play_click():
        set_messages([*messages, "Playing!"])

    return html.div(
        {"className": "Toolbar", "onClick": handle_toolbar_click},
        button(handle_play_click, "Play Movie"),
    )
