from reactpy import component, html, use_state


# start
@component
def todo_list():
    items, set_items = use_state(
        [
            {"id": 0, "text": "Walk the dog"},
            {"id": 1, "text": "Brush the cat"},
        ]
    )
    text, set_text = use_state("")

    def handle_insert(event):
        event.preventDefault()
        if not text:
            return
        # Slicing builds the new list; list.insert() would mutate in place.
        set_items([*items[:1], {"id": 3, "text": text}, *items[1:]])
        set_text("")

    return html.div(
        html.form(
            {"onSubmit": handle_insert},
            html.input(
                {
                    "value": text,
                    "placeholder": "Insert at index 1",
                    "onChange": lambda event: set_text(event["target"]["value"]),
                }
            ),
            html.button({"type": "submit"}, "Insert"),
        ),
        html.ul([html.li({"key": item["id"]}, item["text"]) for item in items]),
    )
