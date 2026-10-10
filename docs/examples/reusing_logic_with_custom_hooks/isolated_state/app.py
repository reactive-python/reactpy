"""Calling a custom Hook twice in one component gives two independent pieces of
state: hooks are matched by call order, not by name.
"""

from reactpy import component, html, use_state


# start
def use_toggle(initial=False):
    on, set_on = use_state(initial)
    return on, (lambda event: set_on(not on))


@component
def panel():
    left, flip_left = use_toggle()
    right, flip_right = use_toggle()
    return html.div(
        html.button({"onClick": flip_left}, f"left {'ON' if left else 'off'}"),
        html.button({"onClick": flip_right}, f"right {'ON' if right else 'off'}"),
        html.p(f"both on: {left and right}"),
    )


@component
def app():
    return panel()
