"""Swapping the reducer function at runtime does nothing — the first one is kept."""

from reactpy import component, html, use_reducer, use_state


# start
def add_by_one(state, action):
    return {"n": state["n"] + 1, "by": "add_by_one"}


def add_by_hundred(state, action):
    return {"n": state["n"] + 100, "by": "add_by_hundred"}


@component
def counter():
    version, set_version = use_state(1)

    # The component body picks a different reducer each time version changes,
    # but use_reducer built its dispatcher on the first render and reuses it.
    reducer = add_by_one if version == 1 else add_by_hundred
    state, dispatch = use_reducer(reducer, {"n": 0, "by": "-"})

    def handle_add(event):
        dispatch({"type": "add"})

    def handle_switch(event):
        set_version(2)

    return html.div(
        html.button({"onClick": handle_add}, "Add"),
        html.button({"onClick": handle_switch}, "Switch reducer"),
        html.p({"id": "readout"}, f"n={state['n']} by={state['by']} version={version}"),
    )


@component
def app():
    return counter()
