from reactpy import component, html

from .my_button import my_button


# start
@component
def my_app():
    return html.div(
        html.h1("Welcome to my app"),
        my_button(),
    )
