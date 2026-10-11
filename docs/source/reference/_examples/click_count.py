import reactpy


@reactpy.component
def ClickCount():
    count, set_count = reactpy.hooks.use_state(0)

    async def handle_click(event):
        set_count(count + 1)

    return reactpy.html.button({"on_click": handle_click}, [f"Click count: {count}"])


reactpy.run(ClickCount)
