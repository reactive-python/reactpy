from reactpy import component, hooks, html
from reactpy.backend.flask import configure
from flask import Flask

# from use_counting_hook import use_counting_hook

def reducer(count, action):
    if action == "increment":
        return count + 1
    elif action == "decrement":
        return count - 1
    elif action == "reset":
        return 0
    else:
        msg = f"Unknown action '{action}'"
        raise ValueError(msg)


@component
def Example_Component():

    count, dispatch = hooks.use_reducer(reducer, 0)

    return html.div(
        f"Count: {count}",
        html.button({"on_click": lambda event: dispatch("reset")}, "Reset"),
        html.button({"on_click": lambda event: dispatch("increment")}, "+"),
        html.button({"on_click": lambda event: dispatch("decrement")}, "-"),
    )



app = Flask(__name__)
configure(app, Example_Component)