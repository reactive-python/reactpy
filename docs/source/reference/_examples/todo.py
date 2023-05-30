import reactpy


@reactpy.component
def Todo():
    items, set_items = reactpy.hooks.use_state([])

    async def add_new_task(event):
        if event["key"] == "Enter":
            set_items([*items, event["target"]["value"]])

    tasks = []

    for index, text in enumerate(items):

        async def remove_task(event, index=index):
            set_items(items[:index] + items[index + 1 :])

        task_text = reactpy.html.td(reactpy.html.p(text))
        delete_button = reactpy.html.td(
            {"on_click": remove_task}, reactpy.html.button(["x"])
        )
        tasks.append(reactpy.html.tr(task_text, delete_button))

    task_input = reactpy.html.input({"on_key_down": add_new_task})
    task_table = reactpy.html.table(tasks)

    return reactpy.html.div(
        reactpy.html.p("press enter to add a task:"),
        task_input,
        task_table,
    )


reactpy.run(Todo)
