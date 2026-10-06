from reactpy import component, html, use_state


# start
@component
def counter():
    score, set_score = use_state(0)

    return html.div(
        {"className": "counter"},
        html.h1(score),
        html.button({"onClick": lambda event: set_score(score + 1)}, "Add one"),
    )


@component
def app():
    # The same component function, rendered at two different positions in the
    # tree. ReactPy tracks state by position, so these two counters each get
    # their own score.
    return html.div(counter(), counter())
