from reactpy import component, html, use_state

# start


@component
def signup():
    signed_up, set_signed_up = use_state(0)
    name, set_name = use_state("")

    async def handle_name_change(event):
        set_name(await event.target.value)

    async def handle_submit(event):
        # Without this line the browser would navigate away from the page.
        event.preventDefault()
        set_signed_up(signed_up + 1)
        set_name("")

    return html.form(
        {"onSubmit": handle_submit},
        html.input({"value": name, "onChange": handle_name_change}),
        html.button({"type": "submit"}, "Sign up"),
        html.p(f"{signed_up} signed up"),
    )
