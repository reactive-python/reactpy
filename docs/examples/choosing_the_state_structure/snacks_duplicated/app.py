"""The selected item duplicated as an object, so editing it desyncs the label."""

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
    selected_item, set_selected_item = use_state(INITIAL_ITEMS[0])

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
                        {"onClick": lambda event, i=item: set_selected_item(i)},
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
