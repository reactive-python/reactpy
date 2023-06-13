from reactpy import component, hooks, html
from reactpy.backend.flask import configure
from flask import Flask

from use_counting_hook import my_first_reactpy_hook




# @component
# def Example_Component():

#     count, dispatch = use_counting_hook(0)

#     return html.div(
#         html.button({"on_click": lambda event: dispatch("reset")}, "Reset"),
#         html.button({"on_click": lambda event: dispatch("increment")}, "add"),
#         html.button({"on_click": lambda event: dispatch("decrement")}, "subtract"),
#         f"Count: {count}"
#     )

@component
def Example_Component():

    count, increment, decrement, reset = my_first_reactpy_hook(10)

    return html.div(
        html.button({"on_click": lambda event: reset()}, "Reset"),
        html.button({"on_click": lambda event: increment()}, "add"),
        html.button({"on_click": lambda event: decrement()}, "subtract"),
        f"Count: {count}"
    )



app = Flask(__name__)
configure(app, Example_Component)