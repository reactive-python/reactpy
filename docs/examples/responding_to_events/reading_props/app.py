from reactpy import component, html, use_state


# start
@component
def alert_button(message, *children):
    shown, set_shown = use_state("")

    async def handle_click(event):
        set_shown(message)

    return html.div(
        html.button({"onClick": handle_click}, *children),
        html.p(shown),
    )


@component
def toolbar():
    return html.div(
        alert_button("Playing!", "Play Movie"),
        alert_button("Uploading!", "Upload Image"),
    )
