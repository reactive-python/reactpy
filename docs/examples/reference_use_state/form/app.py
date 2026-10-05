from reactpy import component, html, use_state


# start
@component
def form():
    first_name, set_first_name = use_state("Ada")
    last_name, set_last_name = use_state("Lovelace")

    return html.div(
        html.label(
            "First name: ",
            html.input(
                {
                    "value": first_name,
                    "onChange": lambda event: set_first_name(event["target"]["value"]),
                }
            ),
        ),
        html.label(
            "Last name: ",
            html.input(
                {
                    "value": last_name,
                    "onChange": lambda event: set_last_name(event["target"]["value"]),
                }
            ),
        ),
        html.h1(f"Hello, {first_name} {last_name}!"),
    )
