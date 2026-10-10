"""Redundant state: `full_name` is stored and re-synced by an Effect."""

from reactpy import component, html, use_effect, use_state


# start
@component
def form():
    first_name, set_first_name = use_state("Ada")
    last_name, set_last_name = use_state("Lovelace")
    # Wrong: this value is not state, it is a calculation of other state.
    full_name, set_full_name = use_state("")

    def effect():
        set_full_name(f"{first_name} {last_name}")

    use_effect(effect, dependencies=[first_name, last_name])

    return html.div(
        html.h1(full_name or "(nothing yet)"),
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
