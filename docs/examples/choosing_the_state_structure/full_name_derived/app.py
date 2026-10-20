"""fullName calculated during render: no second place to keep in sync."""

from reactpy import component, html, use_state


# start
@component
def check_in():
    first_name, set_first_name = use_state("Ada")
    last_name, set_last_name = use_state("Lovelace")

    # Not state. Every render recomputes it from whatever the two fields hold.
    full_name = f"{first_name} {last_name}"

    async def rename_only_first(event):
        set_first_name("Grace")

    async def rename_only_last(event):
        set_last_name("Hopper")

    async def handle_first_name_change(event):
        set_first_name(await event.target.value)

    async def handle_last_name_change(event):
        set_last_name(await event.target.value)

    return html.div(
        html.h2("Let's check you in"),
        html.label(
            "First name: ",
            html.input(
                {
                    "value": first_name,
                    "onChange": handle_first_name_change,
                }
            ),
        ),
        html.br(),
        html.label(
            "Last name: ",
            html.input(
                {
                    "value": last_name,
                    "onChange": handle_last_name_change,
                }
            ),
        ),
        html.br(),
        html.button({"onClick": rename_only_first}, "Rename first"),
        html.button({"onClick": rename_only_last}, "Rename last"),
        html.p({"id": "ticket"}, "Your ticket will be issued to: ", html.b(full_name)),
    )


@component
def app():
    return check_in()
