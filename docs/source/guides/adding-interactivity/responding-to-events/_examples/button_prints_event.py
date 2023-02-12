from idom import component, html, run


@component
def Button():
    def handle_event(event):
        print(event)

    return html.button({"onClick": handle_event}, "Click me!")


run(Button)
