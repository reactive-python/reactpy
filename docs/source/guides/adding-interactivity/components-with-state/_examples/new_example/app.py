from reactpy import component, hooks, html
from reactpy.backend.flask import configure
from flask import Flask

from use_counting_hook import use_counting_hook


@component
def Example_Component():

    number, number, increment, decrement = hooks.use_counting_hook(0)

    return html.div(
        html.button({"on_click": handle_next_click}, "Next"),
        html.h2(f"{number}"),
        html.h2("test")
    )



app = Flask(__name__)
configure(app, Example_Component)