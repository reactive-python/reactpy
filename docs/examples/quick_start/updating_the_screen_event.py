from reactpy import component, html, use_state


# start
@component
def my_button():
    count, set_count = use_state(0)

    def handle_click(event):
        set_count(count + 1)

    return html.button({"onClick": handle_click}, f"Clicked {count} times")
