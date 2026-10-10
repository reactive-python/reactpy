"""The filter runs on every render; use_memo runs it only when inputs change."""

from data import filter_runs, todos

from reactpy import component, html, use_memo, use_state


# start
@component
def todo_list():
    filter_name, set_filter_name = use_state("all")
    new_todo, set_new_todo = use_state("")

    def visible_todos():
        # A real filter over a real dataset. It records every run so the
        # effect of use_memo is countable.
        filter_runs.append(filter_name)
        if filter_name == "all":
            return todos
        if filter_name == "active":
            return [todo for todo in todos if not todo["completed"]]
        return [todo for todo in todos if todo["completed"]]

    shown = use_memo(visible_todos)

    return html.div(
        html.p(f"{len(shown)} of {len(todos)} shown (filter: {filter_name})"),
        html.ul([html.li({"key": todo["id"]}, todo["text"]) for todo in shown]),
        html.button(
            {
                "onClick": lambda event: set_filter_name(
                    {"all": "active", "active": "completed", "completed": "all"}[
                        filter_name
                    ]
                )
            },
            "Change filter",
        ),
        html.input(
            {
                "placeholder": "new todo",
                "value": new_todo,
                "onChange": lambda event: set_new_todo(event["target"]["value"]),
            }
        ),
    )
