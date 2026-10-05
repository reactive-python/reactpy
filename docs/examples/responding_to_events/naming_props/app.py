from reactpy import component, html


# start
@component
def button(on_smash, *children):
    return html.button({"onClick": on_smash}, *children)


@component
def app():
    return html.div(
        button(lambda event: None, "Play Movie"),
        button(lambda event: None, "Upload Image"),
    )
