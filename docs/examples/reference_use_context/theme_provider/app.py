from reactpy import component, create_context, html, use_context, use_state

# start

# One context per concept, created once at module level. The argument is the
# value descendants get when nothing provides one -- a sensible default means
# a component can render before any provider exists.
Theme = create_context("light")


@component
def swatch():
    # Reads whatever the nearest provider above it supplied. It takes no props:
    # the value arrives without anything in between having to pass it along.
    theme = use_context(Theme)
    return html.div(
        html.p(f"theme: {theme}"),
        html.div({"style": {"background": theme, "height": "2rem"}}, ""),
    )


@component
def toolbar():
    # A component in the middle. It neither receives nor cares about `theme`;
    # it only has to render its children for them to reach the provider above.
    return html.div(html.h2("Toolbar"), swatch())


@component
def app():
    theme, set_theme = use_state("light")

    async def handle_theme_click(event):
        set_theme("dark" if theme == "light" else "light")

    return html.div(
        Theme(toolbar(), value=theme),
        html.button(
            {"onClick": handle_theme_click},
            f"Switch to {'dark' if theme == 'light' else 'light'}",
        ),
    )
