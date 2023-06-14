from reactpy import component, hooks, html
from reactpy.backend.flask import configure
from flask import Flask

# Import custom hook from use_counting_hook.py file
from use_counting_hook import use_counting_hook

# Defining a component using the reactpy's component decorator
@component
def Example_Component():

    # Using the custom hook to initialize count, increment, decrement, and reset functions. import them in the same order as they are returned in the hook file
    count, increment, decrement, reset = use_counting_hook(0)

    # The component renders a div which contains three buttons and the current count
    return html.div(
        # Button to reset count, calling reset function on click
        html.button({"on_click": lambda event: reset()}, "Reset"),
        # Button to increment count, calling increment function on click
        html.button({"on_click": lambda event: increment()}, "add"),
        # Button to decrement count, calling decrement function on click
        html.button({"on_click": lambda event: decrement()}, "subtract"),
        # Displaying current count
        f"Count: {count}"
    )

app = Flask(__name__)
configure(app, Example_Component)