from idom import component, html, run


@component
def DataList(items):
    list_item_elements = [html.li(text) for text in items]
    return html.ul(list_item_elements)


@component
def TodoList():
    tasks = [
        "Make breakfast (important)",
        "Feed the dog (important)",
        "Do laundry",
        "Go on a run (important)",
        "Clean the house",
        "Go to the grocery store",
        "Do some coding",
        "Read a book (important)",
    ]
    return html.section(
        html.h1("My Todo List"),
        DataList(tasks),
    )


run(TodoList)
