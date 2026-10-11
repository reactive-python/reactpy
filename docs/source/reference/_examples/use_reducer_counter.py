import reactpy


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


@reactpy.component
def Counter():
    count, dispatch = reactpy.hooks.use_reducer(reducer, 0)

    async def reset_count(event):
        dispatch("reset")

    async def increase_count(event):
        dispatch("increment")

    async def decrease_count(event):
        dispatch("decrement")

    return reactpy.html.div(
        f"Count: {count}",
        reactpy.html.button({"on_click": reset_count}, "Reset"),
        reactpy.html.button({"on_click": increase_count}, "+"),
        reactpy.html.button({"on_click": decrease_count}, "-"),
    )


reactpy.run(Counter)
