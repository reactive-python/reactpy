"""Wrapping a subtree in a provider conditionally throws its state away."""

from reactpy import component, create_context, html, use_context, use_ref, use_state

ThemeContext = create_context("light")


# start
@component
def draft():
    # State owned by the leaf. It is lost if this component is remounted.
    text, set_text = use_state("")
    body = use_ref(0)
    body.current += 1
    return html.div(
        html.input(
            {
                "value": text,
                "onChange": lambda event: set_text(event["target"]["value"]),
                "placeholder": "type something",
            }
        ),
        html.p(
            {"id": "draft"},
            f"draft={text!r} renders={body.current} theme={use_context(ThemeContext)}",
        ),
    )


@component
def panel():
    wrap, set_wrap = use_state(True)
    theme, set_theme = use_state("dark")

    def toggle_wrap(event):
        # Adding or removing the provider changes the shape of the tree, so the
        # subtree below is unmounted and rebuilt: the draft text is lost.
        set_wrap(not wrap)

    def toggle_theme(event):
        # Changing only the value keeps the same tree: the draft survives.
        set_theme("light" if theme == "dark" else "dark")

    return html.div(
        html.button({"onClick": toggle_wrap}, "toggle provider"),
        html.button({"onClick": toggle_theme}, "change value"),
        (ThemeContext(draft(), value=theme) if wrap else draft()),
    )


@component
def app():
    return html.div(html.h3("Provider identity"), panel())
