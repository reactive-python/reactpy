from reactpy import component, html, use_state


@component
def counter(email):
    # A key on this call resets the counter whenever the address changes.
    count, set_count = use_state(0)

    return html.div(
        html.p(f"{email} opened {count} times"),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Open"),
    )


# start
@component
def inbox():
    email, set_email = use_state("ada@example.com")

    return html.div(
        html.button(
            {"onClick": lambda event: set_email("grace@example.com")},
            "Switch account",
        ),
        counter(email, key=email),
    )
