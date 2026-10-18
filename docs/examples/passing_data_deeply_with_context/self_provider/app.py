"""A component cannot read the context it provides itself."""

from reactpy import component, create_context, html, use_context, use_state

ThemeContext = create_context("light")


# start
@component
def label(text):
    return html.p({"id": f"label-{text}"}, f"{text} sees: {use_context(ThemeContext)}")


@component
def section():
    theme, set_theme = use_state("dark")

    async def toggle(event):
        set_theme("light" if theme == "dark" else "dark")

    return html.div(
        html.button({"onClick": toggle}, "toggle"),
        # Reads the context the way any *consumer* does...
        html.p({"id": "self"}, f"section itself sees: {use_context(ThemeContext)}"),
        # ...and provides it for everything below, which is not itself.
        ThemeContext(label("child"), value=theme),
    )


@component
def app():
    return html.div(html.h3("Self-provider"), section(), label("outside"))
