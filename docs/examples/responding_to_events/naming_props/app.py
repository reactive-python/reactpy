from reactpy import component, html, use_state


# start
@component
def button(on_smash, *children):
    return html.button({"onClick": on_smash}, *children)


@component
def app():
    status, set_status = use_state("Nothing selected")

    return html.div(
        html.p(status),
        button(lambda event: set_status("Playing!"), "Play Movie"),
        button(lambda event: set_status("Uploading!"), "Upload Image"),
    )
