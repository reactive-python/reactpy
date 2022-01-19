from idom import html

html.div(
    html.h1("My Todo List"),
    html.ul(
        html.li("Design a cool new app"),
        html.li("Build it"),
        html.li("Share it with the world!"),
    )
)