"""Derived during render: one state variable per real input, nothing else."""

from reactpy import component, html, use_state


# start
@component
def form():
    first_name, set_first_name = use_state("Ada")
    last_name, set_last_name = use_state("Lovelace")
    # Right: calculated during rendering, so it is always in sync.
    full_name = f"{first_name} {last_name}"

    async def handle_first_name_change(event):
        set_first_name(await event.target.value)

    async def handle_last_name_change(event):
        set_last_name(await event.target.value)

    return html.div(
        html.h1(full_name),
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
