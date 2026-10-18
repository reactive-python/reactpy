from reactpy import component, html, use_state


# start
@component
def todo_list():
    items, set_items = use_state(
        [
            {"id": 0, "text": "Walk the dog"},
            {"id": 1, "text": "Brush the cat"},
            {"id": 2, "text": "Teach the fish to juggle"},
        ]
    )

    def handle_delete(id_to_keep):
        async def handler(event):
            # filter() gives a new list; items.remove(...) would mutate it.
            set_items([item for item in items if item["id"] != id_to_keep])

        return handler

    return html.ul(
        [
            html.li(
                {"key": item["id"]},
                item["text"],
                html.button({"onClick": handle_delete(item["id"])}, "Delete"),
            )
            for item in items
        ]
    )
