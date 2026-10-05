from reactpy import component, html, use_state

# start


@component
def broken_toggle():
    """Do not copy this: a hook behind a condition that can change.

    `hidden` occupies slot 1 only while `show` is true. Clicking Toggle makes
    that call disappear, so every hook after it shifts up one slot and starts
    reading somebody else's value -- `count` begins showing the string that
    belongs to `hidden`. No error is raised, on the server or in the browser.
    """
    show, set_show = use_state(True)  # slot 0

    if show:
        hidden, set_hidden = use_state("NOT-A-NUMBER")  # slot 1, conditionally

    count, set_count = use_state(0)  # slot 1 when `show` is False

    return html.div(
        html.h1(count),
        html.p(f"show={show}"),
        html.button({"onClick": lambda event: set_show(not show)}, "Toggle"),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Add 1"),
    )


@component
def fixed_toggle():
    """The same component with the hook order held constant.

    Every hook runs on every render, so the slots stay aligned with the
    variables they belong to. Branching happens in the *return value*, which is
    what rendering is for.
    """
    show, set_show = use_state(True)
    hidden, set_hidden = use_state("NOT-A-NUMBER")
    count, set_count = use_state(0)

    return html.div(
        html.h1(count),
        html.p(f"show={show} hidden={hidden}"),
        html.button({"onClick": lambda event: set_show(not show)}, "Toggle"),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Add 1"),
    )
