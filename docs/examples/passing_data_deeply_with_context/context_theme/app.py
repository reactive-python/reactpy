"""The same four levels, with the theme read from context instead."""

from reactpy import component, create_context, html, use_context, use_state

PLACES = ["Almaty", "Astana", "Shymkent", "Karaganda", "Turkestan"]

# start
ThemeContext = create_context("light")


@component
def place_label(place):
    # Reads the theme directly: no prop had to travel here.
    theme = use_context(ThemeContext)
    color = "coral" if theme == "dark" else "black"
    return html.li({"style": {"color": color}}, place)


@component
def place_list(places):
    # No theme parameter, and none to forward.
    return html.ul([place_label(place) for place in places])


@component
def list_of_places(places):
    return html.div(
        {"style": {"border": "1px solid #ccc", "padding": "8px"}},
        place_list(places),
    )


@component
def section(places):
    return html.section(html.h3("Places"), list_of_places(places))


@component
def app():
    theme, set_theme = use_state("dark")

    def toggle(event):
        set_theme("light" if theme == "dark" else "dark")

    return html.div(
        html.button(
            {"onClick": toggle}, f"Switch to {'light' if theme == 'dark' else 'dark'}"
        ),
        html.p({"id": "theme"}, f"theme={theme}"),
        # The provider is a component: it renders its children with no wrapper.
        ThemeContext(html.div({"id": "places"}, section(PLACES)), value=theme),
    )
