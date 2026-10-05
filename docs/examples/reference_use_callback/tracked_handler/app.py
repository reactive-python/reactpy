from reactpy import component, html, use_callback, use_state

# start


@component
def notes():
    notes_list, set_notes_list = use_state([])
    draft, set_draft = use_state("")

    # List what the handler reads and the cached function is replaced exactly
    # when those values change: the click always sees the current draft, while
    # the identity still stays put between changes.
    add_note = use_callback(
        lambda event=None: set_notes_list([*notes_list, draft]),
        dependencies=[notes_list, draft],
    )

    return html.div(
        html.h1("Notes"),
        html.ul(
            [
                html.li({"key": str(i)}, note or "(blank)")
                for i, note in enumerate(notes_list)
            ]
        ),
        html.input(
            {
                "value": draft,
                "onChange": lambda event: set_draft(event["target"]["value"]),
            }
        ),
        html.button({"onClick": add_note}, "Add note"),
    )
