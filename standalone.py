from reactpy import component, hooks, html
from reactpy.backend.standalone import ReactPy


@component
def Counter():
    count, set_count = hooks.use_state(0)

    def increment(event):
        set_count(count + 1)

    return html.div(
        html.button({"onClick": increment}, "Increment"),
        html.p(f"Count: {count}"),
    )


app = ReactPy(Counter)
# from reactpy import run

# run(Counter)
