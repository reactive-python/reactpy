from reactpy import html

filter_text = ""


def set_filter_text(value): ...


# start
html.input(
    {
        "type": "text",
        "value": filter_text,
        "placeholder": "Search...",
        "onChange": lambda event: set_filter_text(event["target"]["value"]),
    }
)
