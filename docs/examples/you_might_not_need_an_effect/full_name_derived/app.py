"""Derived during render: one state variable per real input, nothing else."""

from reactpy import component, html, use_state


# start
@component
def form():
    first_name, set_first_name = use_state("Ada")
    last_name, set_last_name = use_state("Lovelace")
    # Right: calculated during rendering, so it is always in sync.
    full_name = f"{first_name} {last_name}"

    return html.div(
        html.h1(full_name),
        html.input(
            {
                "value": first_name,
                "onChange": lambda event: set_first_name(event["target"]["value"]),
            }
        ),
        html.input(
            {
                "value": last_name,
                "onChange": lambda event: set_last_name(event["target"]["value"]),
            }
        ),
    )
