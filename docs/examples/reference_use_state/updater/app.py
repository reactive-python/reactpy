from reactpy import component, html, use_state


# start
@component
def counter():
    count, set_count = use_state(0)

    async def handle_add_three(event):
        # Updaters receive the current value, so all three increments land.
        set_count(lambda previous: previous + 1)
        set_count(lambda previous: previous + 1)
        set_count(lambda previous: previous + 1)

    return html.div(
        html.h1(count),
        html.button({"onClick": handle_add_three}, "+3"),
    )
