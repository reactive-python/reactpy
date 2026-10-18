"""The UI: no reducer, no context object, no wiring — just use_tasks()."""

from tasks import task_store, use_tasks

from reactpy import component, html


# start
@component
def task_form(task):
    # No props. The dispatch comes from the wiring file.
    _, dispatch = use_tasks()

    async def handle_toggle(event):
        dispatch({"type": "toggled", "id": task["id"]})

    return html.div(
        {"style": {"textDecoration": "line-through" if task["done"] else "none"}},
        task["text"],
        html.button({"onClick": handle_toggle}, "Toggle"),
    )


@component
def task(task):
    _, dispatch = use_tasks()

    async def handle_delete(event):
        dispatch({"type": "deleted", "id": task["id"]})

    return html.li(
        {"key": task["id"]},
        task_form(task),
        html.button({"onClick": handle_delete}, "Delete"),
    )


@component
def task_list():
    state, _ = use_tasks()
    return html.ul([task(item, key=item["id"]) for item in state["tasks"]])


@component
def task_app():
    state, dispatch = use_tasks()

    async def handle_add(event):
        dispatch({"type": "added"})

    return html.div(
        html.h3("Prague itinerary"),
        html.button({"onClick": handle_add}, "Add task"),
        task_list(),
        html.p({"id": "summary"}, f"{len(state['tasks'])} tasks"),
    )


@component
def app():
    # One name from the wiring file: the provider component.
    return task_store(task_app())
