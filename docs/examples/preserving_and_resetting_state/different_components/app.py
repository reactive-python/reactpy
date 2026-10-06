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
    is_paused, set_is_paused = use_state(False)

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
                    "onChange": lambda event: set_is_paused(event["target"]["checked"]),
                }
            ),
            "Take a break",
        ),
    )
