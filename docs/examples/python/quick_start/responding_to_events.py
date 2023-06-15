from reactpy import component, html


# start
@component
def my_button():
    def handle_click(event):
        print("You clicked me!")

    return html.button(
        {"on_click": handle_click},
        "Click me",
    )
