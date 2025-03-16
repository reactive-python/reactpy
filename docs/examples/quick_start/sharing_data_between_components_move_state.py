from reactpy import component, html, use_state

# start
@component
def my_app():
    count, set_count = use_state(0)

    def handle_click(event):
        set_count(count + 1)

    return html.div(
        html.h1("Counters that update separately"),
        my_button(),
        my_button(),
    )


@component
def my_button():
    # ... we're moving code from here ...
