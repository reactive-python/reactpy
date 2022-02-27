import idom


def reducer(count, action):
    if action == "increment":
        return count + 1
    elif action == "decrement":
        return count - 1
    elif action == "reset":
        return 0
    else:
        raise ValueError(f"Unknown action '{action}'")


@idom.component
def Counter():
    count, dispatch = idom.hooks.use_reducer(reducer, 0)
    return idom.html.div(
        f"Count: {count}",
        idom.html.button({"onClick": lambda event: dispatch("reset")}, "Reset"),
        idom.html.button({"onClick": lambda event: dispatch("increment")}, "+"),
        idom.html.button({"onClick": lambda event: dispatch("decrement")}, "-"),
    )


idom.run(Counter)
