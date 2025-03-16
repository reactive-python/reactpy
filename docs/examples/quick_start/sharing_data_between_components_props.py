from reactpy import component, html, use_state


# start
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
    # end


@component
def my_button(count, on_click):
    ...
