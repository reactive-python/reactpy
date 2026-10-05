from reactpy import component, html, use_state


# start
@component
def form():
    person, set_person = use_state(
        {"firstName": "Jane", "lastName": "Jacobs", "email": "jane@example.com"}
    )

    # One handler for every field. ReactPy always calls a handler with the
    # event as its single positional argument, so the field name is bound by
    # the lambdas below rather than delivered by the client.
    def handle_change(field, event):
        set_person({**person, field: event["target"]["value"]})

    return html.div(
        html.input(
            {
                "value": person["firstName"],
                "onChange": lambda event: handle_change("firstName", event),
            }
        ),
        html.input(
            {
                "value": person["lastName"],
                "onChange": lambda event: handle_change("lastName", event),
            }
        ),
        html.input(
            {
                "value": person["email"],
                "onChange": lambda event: handle_change("email", event),
            }
        ),
        html.hr(),
        html.h1(f"Hello, {person['firstName']} {person['lastName']}!"),
    )
