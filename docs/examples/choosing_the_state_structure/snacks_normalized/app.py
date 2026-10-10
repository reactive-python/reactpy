"""Only the selected id in state; the item itself is looked up during render."""

from reactpy import component, html, use_state

INITIAL_ITEMS = [
    {"id": 0, "title": "pretzels"},
    {"id": 1, "title": "crispy seaweed"},
    {"id": 2, "title": "granola bar"},
]


# start
@component
def menu():
    items, set_items = use_state(INITIAL_ITEMS)
    selected_id, set_selected_id = use_state(0)

    # Derived: there is exactly one copy of the title, and it lives in items.
    selected_item = next(item for item in items if item["id"] == selected_id)

    def handle_item_change(item_id, event):
        new_title = event["target"]["value"]
        set_items(
            [
                {**item, "title": new_title} if item["id"] == item_id else item
                for item in items
            ]
        )

    return html.div(
        html.h2("What's your travel snack?"),
        html.ul(
            [
                html.li(
                    {"key": item["id"]},
                    html.input(
                        {
                            "value": item["title"],
                            "onChange": lambda event, i=item: handle_item_change(
                                i["id"], event
                            ),
                        }
                    ),
                    html.button(
                        {"onClick": lambda event, i=item: set_selected_id(i["id"])},
                        "Choose",
                    ),
                )
                for item in items
            ]
        ),
        html.p({"id": "picked"}, f"You picked {selected_item['title']}."),
    )


@component
def app():
    return menu()
