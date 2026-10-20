"""The nearest provider wins, and a provider only covers its own children."""

from reactpy import component, create_context, html, use_context

ThemeContext = create_context("light")


# start
@component
def deep_label(tag):
    # Three levels down, still no prop in sight.
    return html.p({"id": tag}, f"{tag} sees: {use_context(ThemeContext)}")


@component
def middle():
    return html.div(html.h4("middle"), deep_label("deep"))


@component
def wrapper():
    # An intermediate component that neither receives nor forwards a theme.
    return html.div(html.h4("wrapper"), middle())


@component
def inner_scope():
    return html.div(
        deep_label("inner"),
        # A provider nested inside another one shadows it for its subtree.
        ThemeContext(deep_label("deepest"), value="innermost"),
    )


@component
def app():
    return html.div(
        # Same context, several providers, several scopes.
        deep_label("outside"),
        ThemeContext(wrapper(), value="outer"),
        ThemeContext(inner_scope(), value="middle-provider"),
        deep_label("after"),
    )
