from reactpy import component, html


# start
@component
def search_form():
    return html.form(
        html.input({"id": "search", "type": "search"}),
        # A string in a handler slot runs in the browser (see Responding to
        # Events), which is the only way to reach an element by id.
        html.button(
            {
                "onClick": "document.getElementById('search').focus()",
            },
            "Focus the input",
        ),
    )
