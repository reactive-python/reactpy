from reactpy import component, html, use_state
from reactpy.executors.asgi import ReactPy


@component
def counter():
    count, set_count = use_state(0)

    async def handle_count_click(event):
        set_count(count + 1)

    return html.div(
        html.h1(count),
        html.button({"onClick": handle_count_click}, "Add 1"),
    )


# start
my_app = ReactPy(counter)
