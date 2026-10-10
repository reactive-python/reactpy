"""Four levels of props to reach one label."""

from reactpy import component, html, use_state

# start
PLACES = ["Almaty", "Astana", "Shymkent", "Karaganda", "Turkestan"]


@component
def place_label(place, theme):
    color = "coral" if theme == "dark" else "black"
    return html.li({"style": {"color": color}}, place)


@component
def place_list(places, theme):
    return html.ul([place_label(place, theme) for place in places])


@component
def list_of_places(places, theme):
    # Renders its children inside the list box.
    return html.div(
        {"style": {"border": "1px solid #ccc", "padding": "8px"}},
        place_list(places, theme),
    )


@component
def section(places, theme):
    return html.section(html.h3("Places"), list_of_places(places, theme))


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
        html.div({"id": "places"}, section(PLACES, theme)),
    )
