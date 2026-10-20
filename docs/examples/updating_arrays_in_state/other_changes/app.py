from reactpy import component, html, use_state


# start
@component
def todo_list():
    items, set_items = use_state(
        [
            {"id": 0, "text": "Walk the dog"},
            {"id": 1, "text": "Brush the cat"},
            {"id": 2, "text": "Feed the fish"},
        ]
    )
    log, set_log = use_state([])

    def record(label, next_items):
        set_items(next_items)
        set_log([*log, f"{label}: {', '.join(i['text'] for i in next_items)}"])

    async def handle_reversed_click(event):
        record("reversed", list(reversed(items)))

    async def handle_sorted_click(event):
        record("sorted", sorted(items, key=lambda i: i["text"]))

    async def handle_filtered_click(event):
        record("filtered", items[:2])

    return html.div(
        html.div(
            html.button(
                {"onClick": handle_reversed_click},
                "Reverse",
            ),
            html.button(
                {"onClick": handle_sorted_click},
                "Sort",
            ),
            html.button(
                {"onClick": handle_filtered_click},
                "Keep first two",
            ),
        ),
        html.ul([html.li({"key": item["id"]}, item["text"]) for item in items]),
        html.ul([html.li({"key": i}, line) for i, line in enumerate(log)]),
    )
