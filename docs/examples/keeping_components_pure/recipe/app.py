from reactpy import component, html


# start
@component
def recipe(drinkers):
    return html.ol(
        html.li(f"Boil {drinkers} cups of water."),
        html.li(f"Add {drinkers} spoons of tea and {0.5 * drinkers} spoons of spice."),
        html.li(f"Add {0.5 * drinkers} cups of milk to boil and sugar to taste."),
    )


@component
def app():
    return html.section(
        html.h1("Spiced Chai Recipe"),
        html.h2("For two"),
        recipe(2),
        html.h2("For a gathering"),
        recipe(4),
    )
