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
    is_paused, set_is_paused = use_state(False)

    async def handle_is_paused_change(event):
        set_is_paused(await event.target.checked)

    return html.div(
        # Switching between a counter() and an html.p() puts a *different* kind
        # of child at this position, so ReactPy discards the counter's state
        # and starts a brand new one when the break ends.
        html.p("See you later!") if is_paused else counter(),
        html.label(
            html.input(
                {
                    "type": "checkbox",
                    "checked": is_paused,
                    "onChange": handle_is_paused_change,
                }
            ),
            "Take a break",
        ),
    )
