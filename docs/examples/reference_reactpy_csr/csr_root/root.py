from reactpy import component, html, use_state


@component
def root():
    count, set_count = use_state(0)
    return html.div(
        html.h1(count),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Add 1"),
    )
