"""No provider anywhere: every consumer reads the default."""

from reactpy import component, create_context, html, use_context

# start
ThemeContext = create_context("light")


@component
def label(text):
    theme = use_context(ThemeContext)
    return html.p({"id": f"label-{text}"}, f"{text}: theme={theme}")


@component
def app():
    # Nothing wraps these in ThemeContext, so use_context falls back to the
    # value passed to create_context.
    return html.div(html.h3("No provider"), label("a"), label("b"))
