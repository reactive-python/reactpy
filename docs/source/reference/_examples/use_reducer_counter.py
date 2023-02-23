import reactpy


def reducer(count, action):
    if action == "increment":
        return count + 1
    elif action == "decrement":
        return count - 1
    elif action == "reset":
        return 0
    else:
        raise ValueError(f"Unknown action '{action}'")


@reactpy.component
def Counter():
    count, dispatch = reactpy.hooks.use_reducer(reducer, 0)
    return reactpy.html.div(
        f"Count: {count}",
        reactpy.html.button({"on_click": lambda event: dispatch("reset")}, "Reset"),
        reactpy.html.button({"on_click": lambda event: dispatch("increment")}, "+"),
        reactpy.html.button({"on_click": lambda event: dispatch("decrement")}, "-"),
    )


reactpy.run(Counter)
