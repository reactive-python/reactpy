from reactpy import component, html, use_state


# start
@component
def counter():
    count, set_count = use_state(0)

    def handle_click(event):
        set_count(count + 1)

    return html.button({"onClick": handle_click}, f"You clicked {count} times")
