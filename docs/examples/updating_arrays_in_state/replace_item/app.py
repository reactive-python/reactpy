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

    def handle_replace(event):
        event.preventDefault()
        if not text:
            return
        # Replace one item by building a whole new list. Mutating
        # items[0]["text"] would be invisible to ReactPy.
        set_items([{"id": 0, "text": text}, *items[1:]])
        set_text("")

    return html.div(
        html.form(
            {"onSubmit": handle_replace},
            html.input(
                {
                    "value": text,
                    "placeholder": "Replace the first item",
                    "onChange": lambda event: set_text(event["target"]["value"]),
                }
            ),
            html.button({"type": "submit"}, "Replace"),
        ),
        html.ul([html.li({"key": item["id"]}, item["text"]) for item in items]),
    )
