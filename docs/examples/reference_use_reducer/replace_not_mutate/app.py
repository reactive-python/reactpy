from reactpy import component, html, use_reducer

# start


def counter_reducer(state, action):
    # Always return a NEW object. `use_reducer` is built on `use_state`, which
    # compares what you return against what it already holds and schedules no
    # render when the two are equal. Mutating `state` here and returning it
    # would update the data, schedule nothing, and fail with no error and
    # nothing in the browser console.
    return {**state, "count": state["count"] + 1}


@component
def counter():
    state, dispatch = use_reducer(counter_reducer, {"count": 0})
    return html.div(
        html.h1(state["count"]),
        html.button({"onClick": lambda event: dispatch({"type": "inc"})}, "Add 1"),
    )
