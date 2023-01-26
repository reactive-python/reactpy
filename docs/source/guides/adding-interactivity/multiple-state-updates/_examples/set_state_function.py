from idom import component, html, run, use_state


def increment(old_number):
    new_number = old_number + 1
    return new_number


@component
def Counter():
    number, set_number = use_state(0)

    def handle_click(event):
        set_number(increment)
        set_number(increment)
        set_number(increment)

    return html.div(
        html.h1(number),
        html.button("Increment", on_click=handle_click),
    )


run(Counter)
