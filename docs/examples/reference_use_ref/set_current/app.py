from reactpy import component, html, use_ref, use_state

# start


@component
def theme_picker():
    # `set_current` is the call-shaped version of `ref.current = value`, and it
    # hands back the value it replaced. The return value is what makes the swap
    # below one expression: an assignment cannot be an argument to set_theme().
    previous = use_ref("dark")
    theme, set_theme = use_state("light")

    def pick(name):
        # A factory: it returns a fresh coroutine per button, so each button
        # gets its own handler and the theme it belongs to is bound by closure.
        async def choose_theme(event):
            previous.set_current(theme)  # record the theme being left
            set_theme(name)

        return choose_theme

    async def swap_back(event):
        set_theme(previous.set_current(theme))

    return html.div(
        html.h1(f"{theme} theme"),
        html.p(f"you were just using: {previous.current}"),
        html.button({"onClick": swap_back}, "Swap back"),
        html.button({"onClick": pick("light")}, "Light"),
        html.button({"onClick": pick("dark")}, "Dark"),
    )
