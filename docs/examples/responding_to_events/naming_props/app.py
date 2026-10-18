from reactpy import component, html, use_state


# start
@component
def button(on_smash, *children):
    return html.button({"onClick": on_smash}, *children)


@component
def app():
    status, set_status = use_state("Nothing selected")

    async def handle_play(event):
        set_status("Playing!")

    async def handle_upload(event):
        set_status("Uploading!")

    return html.div(
        html.p(status),
        button(handle_play, "Play Movie"),
        button(handle_upload, "Upload Image"),
    )
