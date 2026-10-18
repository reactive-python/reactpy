from reactpy import component, html, use_state


# start
@component
def form():
    person, set_person = use_state(
        {"firstName": "Jane", "lastName": "Jacobs", "email": "jane@example.com"}
    )

    # One handler for every field. ReactPy always calls a handler with the
    # event as its single positional argument, so the field name is bound by
    # the thin handlers below rather than delivered by the client.
    async def handle_change(field, event):
        set_person({**person, field: await event.target.value})

    async def handle_first_name_change(event):
        await handle_change("firstName", event)

    async def handle_last_name_change(event):
        await handle_change("lastName", event)

    async def handle_email_change(event):
        await handle_change("email", event)

    return html.div(
        html.input(
            {
                "value": person["firstName"],
                "onChange": handle_first_name_change,
            }
        ),
        html.input(
            {
                "value": person["lastName"],
                "onChange": handle_last_name_change,
            }
        ),
        html.input(
            {
                "value": person["email"],
                "onChange": handle_email_change,
            }
        ),
        html.hr(),
        html.h1(f"Hello, {person['firstName']} {person['lastName']}!"),
    )
