from reactpy import component, html, use_state


# start
@component
def counter(is_fancy):
    score, set_score = use_state(0)

    async def handle_score_click(event):
        set_score(score + 1)

    return html.div(
        {"className": f"counter{' fancy' if is_fancy else ''}"},
        html.h1(score),
        html.button({"onClick": handle_score_click}, "Add one"),
    )


@component
def app():
    is_fancy, set_is_fancy = use_state(False)

    async def handle_is_fancy_change(event):
        set_is_fancy(await event.target.checked)

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
                    "onChange": handle_is_fancy_change,
                }
            ),
            "Use fancy styling",
        ),
    )
