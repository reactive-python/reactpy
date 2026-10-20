from reactpy import component, html


@component
def button():
    async def handle_click(event):
        print("You clicked me!")

    return html.button({"onClick": handle_click}, "Click me")
