import reactpy


def increment(last_count):
    return last_count + 1


def decrement(last_count):
    return last_count - 1


@reactpy.component
def Counter():
    initial_count = 0
    count, set_count = reactpy.hooks.use_state(initial_count)

    async def reset_count(event):
        set_count(initial_count)

    async def increase_count(event):
        set_count(increment)

    async def decrease_count(event):
        set_count(decrement)

    return reactpy.html.div(
        f"Count: {count}",
        reactpy.html.button({"on_click": reset_count}, "Reset"),
        reactpy.html.button({"on_click": increase_count}, "+"),
        reactpy.html.button({"on_click": decrease_count}, "-"),
    )


reactpy.run(Counter)
