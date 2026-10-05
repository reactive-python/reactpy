from reactpy import component, html, use_reducer, use_state

# start


@component
def stepper():
    step, set_step = use_state(1)

    def reducer(state, action):
        # BUG: this reducer closes over `step`, but ReactPy builds the
        # dispatcher once, on the first render, and keeps that reducer
        # forever. Bump `step` to 3 and this keeps adding 1.
        return {**state, "total": state["total"] + step}

    state, dispatch = use_reducer(reducer, {"total": 0})

    return html.div(
        html.p(f"total: {state['total']}"),
        html.p(f"step: {step}"),
        html.button({"onClick": lambda event: dispatch({"type": "add"})}, "Add step"),
        html.button({"onClick": lambda event: set_step(step + 1)}, "Bump step"),
    )
