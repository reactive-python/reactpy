"""Keep the provider in the tree; vary only its value, and state survives."""

from reactpy import component, create_context, html, use_context, use_ref, use_state

ThemeContext = create_context("light")


# start
@component
def draft():
    # State owned by the leaf. It survives as long as this component keeps the
    # same position in the tree.
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
    provide, set_provide = use_state(True)
    theme, set_theme = use_state("dark")

    def toggle_wrap(event):
        set_provide(not provide)

    def toggle_theme(event):
        set_theme("light" if theme == "dark" else "dark")

    return html.div(
        html.button({"onClick": toggle_wrap}, "toggle provider"),
        html.button({"onClick": toggle_theme}, "change value"),
        # The provider is always in the tree, so nothing below it is unmounted.
        # "Not provided" is expressed as the default value, not as an absent
        # wrapper.
        ThemeContext(draft(), value=theme if provide else "light"),
    )


@component
def app():
    return html.div(html.h3("Provider always present"), panel())
