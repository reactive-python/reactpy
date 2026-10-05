from reactpy import component, html, use_reducer

# start


def todos_reducer(state, action):
    """One function per behaviour, chosen by the action's type.

    Defined at module level on purpose: ReactPy builds the dispatcher once, on
    the first render, and keeps that reducer -- a reducer defined inside the
    component would keep its first-render closure forever.

    Every branch returns a NEW dict. Returning the mutated `state` would be
    dropped without a word.
    """
    if action["type"] == "add":
        return {
            **state,
            "items": [*state["items"], {"text": action["text"], "done": False}],
        }
    if action["type"] == "toggle":
        items = [
            {**item, "done": not item["done"]} if i == action["index"] else item
            for i, item in enumerate(state["items"])
        ]
        return {**state, "items": items}
    if action["type"] == "clear_done":
        return {**state, "items": [i for i in state["items"] if not i["done"]]}
    return state


@component
def todo_list():
    state, dispatch = use_reducer(todos_reducer, {"items": []})

    return html.div(
        html.h1(f"To-do ({sum(1 for i in state['items'] if not i['done'])} left)"),
        html.ul(
            [
                html.li(
                    {"key": i},
                    html.button(
                        {
                            "onClick": lambda event, i=i: dispatch(
                                {"type": "toggle", "index": i}
                            )
                        },
                        state["items"][i]["text"],
                    ),
                )
                for i in range(len(state["items"]))
            ]
        ),
        html.button(
            {
                "onClick": lambda event: dispatch(
                    {"type": "add", "text": f"task {len(state['items']) + 1}"}
                )
            },
            "Add task",
        ),
        html.button(
            {"onClick": lambda event: dispatch({"type": "clear_done"})}, "Clear done"
        ),
    )
