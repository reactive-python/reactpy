from reactpy import component, html, use_reducer

# start

loads = []  # demo-only: shows how often the initializer actually runs


def load_config():
    """Stand-in for anything slow: reading a file, querying a database."""
    loads.append(1)
    return {"rows": [{"name": n} for n in ("alpha", "beta", "gamma")], "selected": None}


def reducer(state, action):
    if action["type"] == "select":
        return {**state, "selected": action["name"]}
    return state


@component
def report():
    # Pass a function as the initial state and ReactPy calls it once, on the
    # first render. Passing `load_config()` instead would call it on every
    # render and throw every result but the first away.
    state, dispatch = use_reducer(reducer, load_config)

    async def handle_click(event):
        dispatch({"type": "select", "name": state["rows"][0]["name"]})

    return html.div(
        html.h1(f"{len(state['rows'])} rows"),
        html.p(f"selected: {state['selected'] or '-'}"),
        html.p(f"initializer ran {len(loads)} time(s)"),
        html.button(
            {"onClick": handle_click},
            "Select first",
        ),
    )
