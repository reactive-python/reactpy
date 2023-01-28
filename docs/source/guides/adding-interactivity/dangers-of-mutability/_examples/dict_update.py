from idom import component, html, run, use_state


@component
def Form():
    person, set_person = use_state(
        {
            "first_name": "Barbara",
            "last_name": "Hepworth",
            "email": "bhepworth@sculpture.com",
        }
    )

    def handle_first_name_change(event):
        set_person({**person, "first_name": event["target"]["value"]})

    def handle_last_name_change(event):
        set_person({**person, "last_name": event["target"]["value"]})

    def handle_email_change(event):
        set_person({**person, "email": event["target"]["value"]})

    return html.div(
        html.label(
            "First name: ",
            html.input(value=person["first_name"], on_change=handle_first_name_change),
        ),
        html.label(
            "Last name: ",
            html.input(value=person["last_name"], on_change=handle_last_name_change),
        ),
        html.label(
            "Email: ",
            html.input(value=person["email"], on_change=handle_email_change),
        ),
        html.p(f"{person['first_name']} {person['last_name']} {person['email']}"),
    )


run(Form)
