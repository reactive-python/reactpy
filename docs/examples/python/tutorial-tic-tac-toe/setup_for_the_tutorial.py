from reactpy import component, html

# start
@component
def square():
    return html.button({"class_name":"square"}, "X")
