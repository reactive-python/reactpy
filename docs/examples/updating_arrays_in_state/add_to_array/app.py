from reactpy import component, html, use_state


# start
@component
def todo_list():
    items, set_items = use_state([{"id": 0, "text": "Walk the dog"}])
    text, set_text = use_state("")

    async def handle_add(event):
        event.preventDefault()
        if not text:
            return
        # A new list; `items.append(...)` would be silently ignored.
        next_id = max((item["id"] for item in items), default=-1) + 1
        set_items([*items, {"id": next_id, "text": text}])
        set_text("")

    async def handle_text_change(event):
        set_text(await event.target.value)

    return html.div(
        html.form(
            {"onSubmit": handle_add},
            html.input(
                {
                    "value": text,
                    "placeholder": "To do...",
                    "onChange": handle_text_change,
                }
            ),
            html.button({"type": "submit"}, "Add"),
        ),
        html.ul([html.li({"key": item["id"]}, item["text"]) for item in items]),
    )
