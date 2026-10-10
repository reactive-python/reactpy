"""The smallest possible Effect: a mount log, and nothing else."""

from reactpy import component, html, use_effect, use_state


# start
@component
def status_page():
    visit_count, set_visit_count = use_state(0)

    def effect():
        # Runs after this component is on screen. ReactPy runs it in the
        # connection's own task, after the render that scheduled it.
        print("status_page is on screen")

    use_effect(effect, dependencies=[])

    return html.div(
        html.h1("Service status"),
        html.p(f"This page has been opened {visit_count} times."),
        html.button(
            {"onClick": lambda event: set_visit_count(visit_count + 1)},
            "Re-check",
        ),
    )
