from reactpy import component, html, use_ref, use_state

# start


@component
def theme_picker():
    # `ref.current = value` is a statement, so it cannot appear inside the
    # `lambda` a one-line handler needs. `set_current` is the expression-shaped
    # version of the same write, and it hands back the value you replaced --
    # which is exactly what you need to remember the previous choice.
    previous = use_ref("light")
    theme, set_theme = use_state("light")

    def pick(name):
        return lambda event=None: (previous.set_current(theme), set_theme(name))

    return html.div(
        html.h1(f"{theme} theme"),
        html.p(f"you were just using: {previous.current}"),
        html.button({"onClick": pick("light")}, "Light"),
        html.button({"onClick": pick("dark")}, "Dark"),
    )
