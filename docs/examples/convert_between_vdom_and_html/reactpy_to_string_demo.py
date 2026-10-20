from reactpy import html, reactpy_to_string

# start
todo_list = html.div(
    html.h1("My Todo List"),
    html.ul(
        html.li("Build a cool new app"),
        html.li("Share it with the world!"),
    ),
)

print(reactpy_to_string(todo_list))
# <div><h1>My Todo List</h1><ul><li>Build a cool new app</li><li>Share it with the world!</li></ul></div>
# end
