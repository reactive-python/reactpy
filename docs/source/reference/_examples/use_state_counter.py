import reactpy


def increment(last_count):
    return last_count + 1


def decrement(last_count):
    return last_count - 1


@reactpy.component
def Counter():
    initial_count = 0
    count, set_count = reactpy.hooks.use_state(initial_count)
    return reactpy.html.div(
        f"Count: {count}",
        reactpy.html.button(
            {"on_click": lambda event: set_count(initial_count)}, "Reset"
        ),
        reactpy.html.button({"on_click": lambda event: set_count(increment)}, "+"),
        reactpy.html.button({"on_click": lambda event: set_count(decrement)}, "-"),
    )


reactpy.run(Counter)
