import idom


@idom.component
def Todo():
    items, set_items = idom.hooks.use_state([])

    async def add_new_task(event):
        if event["key"] == "Enter":
            set_items(items + [event["value"]])

    tasks = []

    for index, text in enumerate(items):

        async def remove_task(event, index=index):
            set_items(items[:index] + items[index + 1 :])

        task_text = idom.html.td(idom.html.p(text))
        delete_button = idom.html.td({"onClick": remove_task}, idom.html.button(["x"]))
        tasks.append(idom.html.tr(task_text, delete_button))

    task_input = idom.html.input({"onKeyDown": add_new_task})
    task_table = idom.html.table(tasks)

    return idom.html.div(task_input, task_table)


idom.run(Todo)
