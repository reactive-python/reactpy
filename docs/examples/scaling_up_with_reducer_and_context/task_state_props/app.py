"""State and dispatch threaded down through components that only forward them."""

from reactpy import component, html, use_reducer

INITIAL_TASKS = [
    {"id": 0, "text": "Packing", "done": False},
    {"id": 1, "text": "Passport", "done": True},
]


def tasks_reducer(state, action):
    kind = action["type"]
    if kind == "added":
        task = {"id": state["next_id"], "text": "New task", "done": False}
        return {
            **state,
            "tasks": [*state["tasks"], task],
            "next_id": state["next_id"] + 1,
        }
    if kind == "toggled":
        return {
            **state,
            "tasks": [
                {**task, "done": not task["done"]}
                if task["id"] == action["id"]
                else task
                for task in state["tasks"]
            ],
        }
    if kind == "deleted":
        return {
            **state,
            "tasks": [task for task in state["tasks"] if task["id"] != action["id"]],
        }
    raise ValueError(f"unknown action type {kind!r}")


# start
@component
def task_form(state, dispatch, task):
    # The only component that actually wants dispatch...
    def handle_toggle(event):
        dispatch({"type": "toggled", "id": task["id"]})

    return html.div(
        {"style": {"textDecoration": "line-through" if task["done"] else "none"}},
        task["text"],
        html.button({"onClick": handle_toggle}, "Toggle"),
    )


@component
def task(state, dispatch, task):
    # ...but must receive it and hand it on, unchanged.
    def handle_delete(event):
        dispatch({"type": "deleted", "id": task["id"]})

    return html.li(
        {"key": task["id"]},
        task_form(state, dispatch, task),
        html.button({"onClick": handle_delete}, "Delete"),
    )


@component
def task_list(state, dispatch):
    # ...and this one forwards both, without reading either.
    return html.ul(
        [task(state, dispatch, item, key=item["id"]) for item in state["tasks"]]
    )


@component
def task_app():
    state, dispatch = use_reducer(tasks_reducer, {"tasks": INITIAL_TASKS, "next_id": 2})

    def handle_add(event):
        dispatch({"type": "added"})

    return html.div(
        html.h3("Prague itinerary"),
        html.button({"onClick": handle_add}, "Add task"),
        task_list(state, dispatch),
        html.p({"id": "summary"}, f"{len(state['tasks'])} tasks"),
    )


@component
def app():
    return task_app()
