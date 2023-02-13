from idom import component, html, run, use_state


@component
def Definitions():
    term_to_add, set_term_to_add = use_state(None)
    definition_to_add, set_definition_to_add = use_state(None)
    all_terms, set_all_terms = use_state({})

    def handle_term_to_add_change(event):
        set_term_to_add(event["target"]["value"])

    def handle_definition_to_add_change(event):
        set_definition_to_add(event["target"]["value"])

    def handle_add_click(event):
        if term_to_add and definition_to_add:
            set_all_terms({**all_terms, term_to_add: definition_to_add})
            set_term_to_add(None)
            set_definition_to_add(None)

    def make_delete_click_handler(term_to_delete):
        def handle_click(event):
            set_all_terms({t: d for t, d in all_terms.items() if t != term_to_delete})

        return handle_click

    return html.div(
        html.button({"onClick": handle_add_click}, "add term"),
        html.label(
            "Term: ",
            html.input({"value": term_to_add, "onChange": handle_term_to_add_change}),
        ),
        html.label(
            "Definition: ",
            html.input(
                {
                    "value": definition_to_add,
                    "onChange": handle_definition_to_add_change,
                }
            ),
        ),
        html.hr(),
        [
            html.div(
                {"key": term},
                html.button(
                    {"onClick": make_delete_click_handler(term)}, "delete term"
                ),
                html.dt(term),
                html.dd(definition),
            )
            for term, definition in all_terms.items()
        ],
    )


run(Definitions)
