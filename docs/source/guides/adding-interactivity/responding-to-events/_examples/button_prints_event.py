from idom import component, html, run


@component
def Button():
    def handle_event(event):
        print(event)

    return html.button("Click me!", on_click=handle_event)


run(Button)
