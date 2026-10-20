from reactpy import component, html, use_state


# start
@component
def text_field():
    first_name, set_first_name = use_state("Ada")

    async def handle_first_name_change(event):
        set_first_name(await event.target.value)

    return html.div(
        html.input(
            {
                "value": first_name,
                "onChange": handle_first_name_change,
            }
        ),
        html.h1(f"Hello, {first_name}!"),
    )
