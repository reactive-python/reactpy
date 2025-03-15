from reactpy import component, html


@component
def my_button():
    return html.button("I'm a button!")


@component
def my_app():
    return html.div(
        html.h1("Welcome to my app"),
        my_button(),
    )
