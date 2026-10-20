from reactpy import component, html


# start
@component
def search_form():
    return html.form(
        html.label({"htmlFor": "search"}, "Search"),
        html.input({"id": "search", "type": "search", "autoFocus": True}),
    )
