from reactpy import html

filter_text = ""


def set_filter_text(value): ...


# start
async def handle_filter_text_change(event):
    set_filter_text(await event.target.value)


html.input(
    {
        "type": "text",
        "value": filter_text,
        "placeholder": "Search...",
        "onChange": handle_filter_text_change,
    }
)
