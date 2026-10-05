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

    def handle_click(event):
        # map() becomes a comprehension; the old items stay untouched.
        set_items([{"id": item["id"], "text": item["text"] + "!"} for item in items])

    return html.div(
        html.button({"onClick": handle_click}, "Add !"),
        html.ul([html.li({"key": item["id"]}, item["text"]) for item in items]),
    )
