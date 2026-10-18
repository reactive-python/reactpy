"""Business logic parked in an Effect, driven by state that only exists to
trigger it — which makes a second click silently do nothing.
"""

from reactpy import component, html, use_effect, use_state


# start
def calculate_shipping(city, country):
    """Plain function: takes what it needs, returns the result."""
    if not city or not country:
        return ""
    return f"{city}, {country} — ${15 + 5}"


@component
def shipping_form():
    city, set_city = use_state("")
    country, set_country = use_state("")
    # state that exists purely to make the Effect run
    quoted, set_quoted = use_state(False)
    shipping_info, set_shipping_info = use_state("")
    clicks, set_clicks = use_state(0)

    async def submit(event):
        set_clicks(clicks + 1)
        set_quoted(True)

    # the "intent" is buried in an Effect watching a flag a click merely sets
    def recalculate():
        if quoted:
            result = calculate_shipping(city, country)
            set_shipping_info(result)
            if result:
                print(f"quoted {result}")

    use_effect(recalculate, dependencies=[quoted])

    async def handle_city_change(e):
        set_city(await e.target.value)

    async def handle_country_change(e):
        set_country(await e.target.value)

    return html.div(
        html.label(
            "City: ",
            html.input({"value": city, "onChange": handle_city_change}),
        ),
        html.label(
            "Country: ",
            html.input(
                {
                    "value": country,
                    "onChange": handle_country_change,
                }
            ),
        ),
        html.button({"onClick": submit}, "Get quote"),
        html.p(shipping_info or "—"),
        f"Clicks: {clicks}",
    )


@component
def app():
    return shipping_form()
