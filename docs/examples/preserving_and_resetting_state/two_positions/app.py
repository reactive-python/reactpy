from reactpy import component, html, use_state


# start
@component
def counter():
    score, set_score = use_state(0)

    async def handle_score_click(event):
        set_score(score + 1)

    return html.div(
        {"className": "counter"},
        html.h1(score),
        html.button({"onClick": handle_score_click}, "Add one"),
    )


@component
def app():
    # The same component function, rendered at two different positions in the
    # tree. ReactPy tracks state by position, so these two counters each get
    # their own score.
    return html.div(counter(), counter())
