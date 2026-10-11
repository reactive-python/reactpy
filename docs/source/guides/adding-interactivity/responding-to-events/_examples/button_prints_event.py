from reactpy import component, html, run


@component
def Button():
    async def handle_event(event):
        print(event)

    return html.button({"on_click": handle_event}, "Click me!")


run(Button)
