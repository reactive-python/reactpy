from reactpy import component, html, run


@component
def Button():
    return html.button("I don't do anything yet")


run(Button)
