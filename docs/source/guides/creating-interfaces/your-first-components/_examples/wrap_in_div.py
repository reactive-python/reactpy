from idom import component, html, run


@component
def MyTodoList():
    return html.div(
        html.h1("My Todo List"),
        html.img(src="https://picsum.photos/id/0/500/300"),
        html.ul(html.li("The first thing I need to do is...")),
    )


run(MyTodoList)
