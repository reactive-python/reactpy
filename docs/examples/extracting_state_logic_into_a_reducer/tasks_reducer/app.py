"""The same three handlers, now describing what the user did."""

from reactpy import component, html, use_reducer

# start
INITIAL_TASKS = [
    {"id": 0, "text": "Packing", "done": False},
    {"id": 1, "text": "Passport", "done": True},
    {"id": 2, "text": "Camera", "done": False},
]


def tasks_reducer(state, action):
    """One place that knows how the task list may change."""
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
                (
                    {**task, "done": not task["done"]}
                    if task["id"] == action["id"]
                    else task
                )
                for task in state["tasks"]
            ],
        }
    if kind == "deleted":
        return {
            **state,
            "tasks": [task for task in state["tasks"] if task["id"] != action["id"]],
        }
    raise ValueError(f"unknown action type {kind!r}")


@component
def task_app():
    state, dispatch = use_reducer(tasks_reducer, {"tasks": INITIAL_TASKS, "next_id": 3})

    async def handle_add_task(event):
        dispatch({"type": "added"})

    def handle_toggle(task_id):
        async def handle_click(event):
            dispatch({"type": "toggled", "id": task_id})

        return handle_click

    def handle_delete(task_id):
        async def handle_click(event):
            dispatch({"type": "deleted", "id": task_id})

        return handle_click

    return html.div(
        html.h3("Prague itinerary"),
        html.button({"onClick": handle_add_task}, "Add task"),
        html.ul(
            [
                html.li(
                    {"key": task["id"]},
                    html.span(
                        {
                            "style": {
                                "textDecoration": (
                                    "line-through" if task["done"] else "none"
                                )
                            }
                        },
                        task["text"],
                    ),
                    html.button({"onClick": handle_toggle(task["id"])}, "Toggle"),
                    html.button({"onClick": handle_delete(task["id"])}, "Delete"),
                )
                for task in state["tasks"]
            ]
        ),
        html.p(
            {"id": "summary"},
            f"{len(state['tasks'])} tasks, next id {state['next_id']}",
        ),
    )


@component
def app():
    return task_app()
