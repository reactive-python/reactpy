from reactpy import component, html, use_callback, use_state

# start


@component
def notes():
    notes_list, set_notes_list = use_state([])
    draft, set_draft = use_state("")

    # List what the handler reads and the cached function is replaced exactly
    # when those values change: the click always sees the current draft, while
    # the identity still stays put between changes.
    async def add_note_handler(event):
        set_notes_list([*notes_list, draft])

    add_note = use_callback(add_note_handler, dependencies=[notes_list, draft])

    async def handle_draft_change(event):
        set_draft(await event.target.value)

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
                "onChange": handle_draft_change,
            }
        ),
        html.button({"onClick": add_note}, "Add note"),
    )
