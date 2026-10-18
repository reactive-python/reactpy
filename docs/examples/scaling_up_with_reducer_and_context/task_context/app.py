"""State and dispatch reach the leaves through context, not props."""

from tasks import INITIAL_STATE, TaskContext, tasks_reducer

from reactpy import component, html, use_context, use_reducer


# start
@component
def task_form(task):
    # Reads dispatch from context; no prop arrived.
    _, dispatch = use_context(TaskContext)

    async def handle_toggle(event):
        dispatch({"type": "toggled", "id": task["id"]})

    return html.div(
        {"style": {"textDecoration": "line-through" if task["done"] else "none"}},
        task["text"],
        html.button({"onClick": handle_toggle}, "Toggle"),
    )


@component
def task(task):
    _, dispatch = use_context(TaskContext)

    async def handle_delete(event):
        dispatch({"type": "deleted", "id": task["id"]})

    return html.li(
        {"key": task["id"]},
        task_form(task),
        html.button({"onClick": handle_delete}, "Delete"),
    )


@component
def task_list():
    # Reads only the state; dispatch never has to come through here.
    state, _ = use_context(TaskContext)
    return html.ul([task(item, key=item["id"]) for item in state["tasks"]])


@component
def task_app():
    state, dispatch = use_reducer(tasks_reducer, INITIAL_STATE)

    async def handle_add(event):
        dispatch({"type": "added"})

    return html.div(
        html.h3("Prague itinerary"),
        html.button({"onClick": handle_add}, "Add task"),
        # One provider for the whole subtree.
        TaskContext(task_list(), value=(state, dispatch)),
        html.p({"id": "summary"}, f"{len(state['tasks'])} tasks"),
    )


@component
def app():
    return task_app()
