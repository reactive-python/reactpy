from idom import component, html, run


@component
def Button():
    def handle_event(event):
        print(event)

    return html.button({"on_click": handle_event}, "Click me!")


run(Button)
