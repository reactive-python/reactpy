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

    async def handle_first_name_change(event):
        set_first_name(await event.target.value)

    async def handle_last_name_change(event):
        set_last_name(await event.target.value)

    return html.div(
        html.h1(full_name or "(nothing yet)"),
        html.input(
            {
                "value": first_name,
                "onChange": handle_first_name_change,
            }
        ),
        html.input(
            {
                "value": last_name,
                "onChange": handle_last_name_change,
            }
        ),
    )
