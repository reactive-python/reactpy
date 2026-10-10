"""Two event handlers share logic; there is no Effect between them."""

from reactpy import component, html, use_state


# start
@component
def shipping_form():
    shipping_city, set_shipping_city = use_state("")
    billing_city, set_billing_city = use_state("")

    def handle_shipping_change(event):
        city = event["target"]["value"]
        set_shipping_city(city)
        # Shared logic: just call the other setter. Handlers are ordinary
        # functions; there is nothing to schedule and nothing to re-sync.
        set_billing_city(city)

    return html.div(
        html.p(f"shipping: {shipping_city or '(empty)'}"),
        html.p(f"billing:  {billing_city or '(empty)'}"),
        html.input(
            {"value": shipping_city, "onChange": handle_shipping_change},
        ),
        html.input(
            {
                "value": billing_city,
                "onChange": lambda event: set_billing_city(event["target"]["value"]),
            }
        ),
    )


# end
