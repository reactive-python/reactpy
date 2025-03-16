from reactpy import component, html


@component
def hello_world():
    return html.div("Hello World")
