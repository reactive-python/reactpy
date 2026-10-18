from reactpy import component, html, use_state


@component
def counter(email):
    # A key on this call resets the counter whenever the address changes.
    count, set_count = use_state(0)

    async def handle_count_click(event):
        set_count(count + 1)

    return html.div(
        html.p(f"{email} opened {count} times"),
        html.button({"onClick": handle_count_click}, "Open"),
    )


# start
@component
def inbox():
    email, set_email = use_state("ada@example.com")

    async def handle_email_click(event):
        set_email("grace@example.com")

    return html.div(
        html.button(
            {"onClick": handle_email_click},
            "Switch account",
        ),
        counter(email, key=email),
    )
