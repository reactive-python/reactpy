from reactpy import component, html


# start
@component
def my_button():
    return html.button("I'm a button!")
