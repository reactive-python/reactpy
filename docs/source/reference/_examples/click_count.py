import idom


@idom.component
def ClickCount():
    count, set_count = idom.hooks.use_state(0)

    return idom.html.button(
        {"on_click": lambda event: set_count(count + 1)}, [f"Click count: {count}"]
    )


idom.run(ClickCount)
