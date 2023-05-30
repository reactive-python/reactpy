from reactpy import component, html, run


@component
def DataList(items, filter_by_priority=None, sort_by_priority=False):
    if filter_by_priority is not None:
        items = [i for i in items if i["priority"] <= filter_by_priority]
    if sort_by_priority:
        items = sorted(items, key=lambda i: i["priority"])
    list_item_elements = [html.li(i["text"]) for i in items]
    return html.ul(list_item_elements)


@component
def TodoList():
    tasks = [
        {"text": "Make breakfast", "priority": 0},
        {"text": "Feed the dog", "priority": 0},
        {"text": "Do laundry", "priority": 2},
        {"text": "Go on a run", "priority": 1},
        {"text": "Clean the house", "priority": 2},
        {"text": "Go to the grocery store", "priority": 2},
        {"text": "Do some coding", "priority": 1},
        {"text": "Read a book", "priority": 1},
    ]
    return html.section(
        html.h1("My Todo List"),
        DataList(tasks, filter_by_priority=1, sort_by_priority=True),
    )


run(TodoList)
