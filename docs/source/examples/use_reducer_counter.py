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


@idom.element
def Counter(initial_count):
    count, dispatch = idom.hooks.use_reducer(reducer, initial_count)
    return idom.html.div(
        f"Count: {count}",
        idom.html.button({"onClick": lambda event: dispatch("reset")}, "Reset"),
        idom.html.button({"onClick": lambda event: dispatch("increment")}, "+"),
        idom.html.button({"onClick": lambda event: dispatch("decrement")}, "-"),
    )


display(Counter, 0)
