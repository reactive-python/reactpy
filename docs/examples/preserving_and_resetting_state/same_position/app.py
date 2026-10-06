from reactpy import component, html, use_state


# start
@component
def counter(is_fancy):
    score, set_score = use_state(0)

    return html.div(
        {"className": f"counter{' fancy' if is_fancy else ''}"},
        html.h1(score),
        html.button({"onClick": lambda event: set_score(score + 1)}, "Add one"),
    )


@component
def app():
    is_fancy, set_is_fancy = use_state(False)

    return html.div(
        # Only one counter() is ever rendered at this position, and it is the
        # same component function either way, so ReactPy keeps its state across
        # the toggle; only the is_fancy prop changes.
        counter(is_fancy),
        html.label(
            html.input(
                {
                    "type": "checkbox",
                    "checked": is_fancy,
                    "onChange": lambda event: set_is_fancy(event["target"]["checked"]),
                }
            ),
            "Use fancy styling",
        ),
    )
