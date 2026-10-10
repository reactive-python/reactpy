"""The same quote logic as an ordinary function called by the event handler:
no trigger state, no Effect, one render per click.

# start
"""

from reactpy import component, html, use_state


def calculate_shipping(city, country):
    """Plain function: takes what it needs, returns the result."""
    if not city or not country:
        return ""
    return f"{city}, {country} — ${15 + 5}"


@component
def shipping_form():
    city, set_city = use_state("")
    country, set_country = use_state("")
    shipping_info, set_shipping_info = use_state("")
    clicks, set_clicks = use_state(0)

    def submit(event):
        set_clicks(clicks + 1)
        result = calculate_shipping(city, country)
        set_shipping_info(result)
        if result:
            print(f"quoted {result}")

    return html.div(
        html.label(
            "City: ",
            html.input(
                {"value": city, "onChange": lambda e: set_city(e["target"]["value"])}
            ),
        ),
        html.label(
            "Country: ",
            html.input(
                {
                    "value": country,
                    "onChange": lambda e: set_country(e["target"]["value"]),
                }
            ),
        ),
        html.button({"onClick": submit}, "Get quote"),
        html.p(shipping_info or "—"),
        f"Clicks: {clicks}",
    )


# end


@component
def app():
    return shipping_form()
