"""fullName stored in state: every writer must remember to update it."""

from reactpy import component, html, use_state


# start
@component
def check_in():
    first_name, set_first_name = use_state("Ada")
    last_name, set_last_name = use_state("Lovelace")
    full_name, set_full_name = use_state("Ada Lovelace")

    def handle_first_name_change(event):
        set_first_name(event["target"]["value"])
        set_full_name(event["target"]["value"] + " " + last_name)

    def handle_last_name_change(event):
        set_last_name(event["target"]["value"])
        set_full_name(first_name + " " + event["target"]["value"])

    def rename_only_first(event):
        # The bug the extra state variable invites: one writer, one update.
        set_first_name("Grace")

    def rename_only_last(event):
        # This one does not touch full_name either.
        set_last_name("Hopper")

    return html.div(
        html.h2("Let's check you in"),
        html.label(
            {},
            "First name: ",
            html.input({"value": first_name, "onChange": handle_first_name_change}),
        ),
        html.br(),
        html.label(
            {},
            "Last name: ",
            html.input({"value": last_name, "onChange": handle_last_name_change}),
        ),
        html.br(),
        html.button({"onClick": rename_only_first}, "Rename first"),
        html.button({"onClick": rename_only_last}, "Rename last"),
        html.p({"id": "ticket"}, "Your ticket will be issued to: ", html.b(full_name)),
    )


@component
def app():
    return check_in()
