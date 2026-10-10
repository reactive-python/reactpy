"""Pass a plain function down; the child calls it on the user's action."""

from reactpy import component, html, use_state


# start
@component
def search_box(on_search):
    query, set_query = use_state("")

    def handle_submit(event):
        event.preventDefault()
        # Not an Effect: the search happens because the user submitted.
        on_search(query)

    return html.form(
        {"onSubmit": handle_submit},
        html.input(
            {
                "value": query,
                "placeholder": "search",
                "onChange": lambda event: set_query(event["target"]["value"]),
            }
        ),
        html.button({"type": "submit"}, "Search"),
    )


@component
def app():
    results, set_results = use_state("Type something and submit.")

    def handle_search(query):
        set_results(f"searching for {query!r}..." if query else "empty query")

    return html.div(html.p(results), search_box(handle_search))


# end
