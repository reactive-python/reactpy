import reactpy


@reactpy.component
def ClickCount():
    count, set_count = reactpy.hooks.use_state(0)

    return reactpy.html.button(
        {"on_click": lambda event: set_count(count + 1)}, [f"Click count: {count}"]
    )


reactpy.run(ClickCount)
