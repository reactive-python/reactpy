from reactpy import component, html, use_state


# start
@component
def form():
    person, set_person = use_state(
        {
            "firstName": "Jane",
            "lastName": "Jacobs",
            "email": "jane@example.com",
            "shippingAddress": {
                "street": "123 Maple Street",
                "city": "Pretendville",
            },
        }
    )

    def handle_city(event):
        address = {**person["shippingAddress"], "city": event["target"]["value"]}
        set_person({**person, "shippingAddress": address})

    return html.div(
        html.label(
            "City: ",
            html.input(
                {
                    "value": person["shippingAddress"]["city"],
                    "onChange": handle_city,
                }
            ),
        ),
        html.h1(person["firstName"]),
        html.p(person["shippingAddress"]["street"]),
        html.p(person["shippingAddress"]["city"]),
    )
