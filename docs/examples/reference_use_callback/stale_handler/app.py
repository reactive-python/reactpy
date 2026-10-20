from reactpy import component, html, use_callback, use_state

# start


@component
def notes():
    notes_list, set_notes_list = use_state([])
    draft, set_draft = use_state("")

    # `draft` is read here, but `dependencies=[]` promises the function never
    # changes -- so ReactPy keeps handing back the *first* function, which
    # closed over an empty `draft`. Each click adds a blank note no matter what
    # you typed. Listing what the handler reads is what fixes it.
    async def add_note_handler(event):
        set_notes_list([*notes_list, draft])

    add_note = use_callback(add_note_handler, dependencies=[])

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
