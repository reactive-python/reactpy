import idom


def incr(last_count):
    return last_count + 1


def decr(last_count):
    return last_count - 1


@idom.element
async def Counter(initial_count):
    count, set_count = idom.hooks.use_state(initial_count)
    return idom.html.div(
        f"Count: {count}",
        idom.html.button({"onClick": lambda event: set_count(initial_count)}, "Reset"),
        idom.html.button({"onClick": lambda event: set_count(incr)}, "+"),
        idom.html.button({"onClick": lambda event: set_count(decr)}, "-"),
    )


display(Counter, 0)
