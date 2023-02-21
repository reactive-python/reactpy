from idom import component, html, run


@component
def PrintButton(display_text, message_text):
    def handle_event(event):
        print(message_text)

    return html.button({"on_click": handle_event}, display_text)


@component
def App():
    return html.div(
        PrintButton("Play", "Playing"),
        PrintButton("Pause", "Paused"),
    )


run(App)
