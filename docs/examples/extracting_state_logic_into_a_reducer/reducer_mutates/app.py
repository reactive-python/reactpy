"""A reducer that mutates: ReactPy never re-renders, and never warns."""

from reactpy import component, html, use_reducer

# start
INITIAL_TASKS = [
    {"id": 0, "text": "Packing", "done": False},
    {"id": 1, "text": "Passport", "done": True},
]


def mutating_reducer(state, action):
    """Looks fine, edits the list in place, returns it. Nothing will re-render."""
    if action["type"] == "added":
        state["tasks"].append(
            {"id": state["next_id"], "text": "New task", "done": False}
        )
        return state
    return state


@component
def task_app():
    # A fresh list per component instance: this reducer mutates the list it is
    # given, so it must not be handed a module-level one.
    state, dispatch = use_reducer(
        mutating_reducer, {"tasks": [*INITIAL_TASKS], "next_id": 2}
    )

    def handle_add_task(event):
        dispatch({"type": "added"})

    return html.div(
        html.button({"onClick": handle_add_task}, "Add task"),
        html.ul(
            [html.li({"key": task["id"]}, task["text"]) for task in state["tasks"]]
        ),
        html.p({"id": "summary"}, f"{len(state['tasks'])} tasks rendered"),
    )


@component
def app():
    return task_app()
