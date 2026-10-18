"""Three handlers that each rebuild the task list themselves."""

from reactpy import component, html, use_state

# start
INITIAL_TASKS = [
    {"id": 0, "text": "Packing", "done": False},
    {"id": 1, "text": "Passport", "done": True},
    {"id": 2, "text": "Camera", "done": False},
]


@component
def task_app():
    next_id, set_next_id = use_state(3)
    tasks, set_tasks = use_state(INITIAL_TASKS)

    async def handle_add_task(event):
        set_tasks([*tasks, {"id": next_id, "text": "New task", "done": False}])
        set_next_id(next_id + 1)

    def handle_toggle(task_id):
        async def handle_click(event):
            set_tasks(
                [
                    (
                        {**task, "done": not task["done"]}
                        if task["id"] == task_id
                        else task
                    )
                    for task in tasks
                ]
            )

        return handle_click

    def handle_delete(task_id):
        async def handle_click(event):
            set_tasks([task for task in tasks if task["id"] != task_id])

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
                for task in tasks
            ]
        ),
        html.p({"id": "summary"}, f"{len(tasks)} tasks, next id {next_id}"),
    )


@component
def app():
    return task_app()
