from reactpy import component, html


# start
@component
def square():
    return html.button({"className": "square"}, "X")
