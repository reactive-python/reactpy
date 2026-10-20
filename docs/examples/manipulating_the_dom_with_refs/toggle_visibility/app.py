from reactpy import component, html, use_state


# start
@component
def todo_list():
    shown, set_shown = use_state(True)

    async def handle_shown_click(event):
        set_shown(not shown)

    return html(
        html.div(
            {"id": "todo", "hidden": not shown},
            html.p("Learn ReactPy"),
            html.p("Build something"),
        ),
        html.button(
            {"onClick": handle_shown_click},
            "Hide" if shown else "Show",
        ),
    )
