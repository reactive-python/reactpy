from reactpy import component, html, use_state


# start
@component
def form():
    person, set_person = use_state(
        {
            "firstName": "Jane",
            "lastName": "Jacobs",
            "email": "jane@example.com",
        }
    )

    def handle_first_name(event):
        # Copy everything, then override just this one field.
        set_person({**person, "firstName": event["target"]["value"]})

    def handle_last_name(event):
        set_person({**person, "lastName": event["target"]["value"]})

    def handle_email(event):
        set_person({**person, "email": event["target"]["value"]})

    return html.div(
        html.input({"value": person["firstName"], "onChange": handle_first_name}),
        html.input({"value": person["lastName"], "onChange": handle_last_name}),
        html.input({"value": person["email"], "onChange": handle_email}),
        html.hr(),
        html.h1(f"Hello, {person['firstName']} {person['lastName']}!"),
        html.a({"href": f"mailto:{person['email']}"}, person["email"]),
    )
