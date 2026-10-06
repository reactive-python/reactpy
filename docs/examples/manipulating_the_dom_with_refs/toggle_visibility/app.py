from reactpy import component, html, use_state


# start
@component
def todo_list():
    shown, set_shown = use_state(True)

    return html(
        html.div(
            {"id": "todo", "hidden": not shown},
            html.p("Learn ReactPy"),
            html.p("Build something"),
        ),
        html.button(
            {"onClick": lambda event: set_shown(not shown)},
            "Hide" if shown else "Show",
        ),
    )
