from idom import component, html, run


@component
def App():
    return html.div(
        html.h1("My Todo List"),
        html.ul(
            html.li("Build a cool new app"),
            html.li("Share it with the world!"),
        ),
    )


run(App)
