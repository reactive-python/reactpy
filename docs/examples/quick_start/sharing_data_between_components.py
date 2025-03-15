from reactpy import component, html, use_state


@component
def my_app():
    count, set_count = use_state(0)

    def handle_click(event):
        set_count(count + 1)

    return html.div(
        html.h1("Counters that update together"),
        my_button(count, handle_click),
        my_button(count, handle_click),
    )


@component
def my_button(count, on_click):
    return html.button({"onClick": on_click}, f"Clicked {count} times")
