from reactpy import component, html, use_state


def create_expensive_state():
    # Runs once, on the first render only -- not on every re-render.
    return {"items": [f"item {i}" for i in range(1000)]}


# start
@component
def list_page():
    state, set_state = use_state(create_expensive_state)

    return html.div(
        html.h1(f"{len(state['items'])} items"),
        html.p(state["items"][0]),
    )
