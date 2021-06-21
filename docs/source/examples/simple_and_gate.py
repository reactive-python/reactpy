import idom


@idom.component
def AndGate():
    input_1, toggle_1 = use_toggle()
    input_2, toggle_2 = use_toggle()
    return idom.html.div(
        idom.html.input({"type": "checkbox", "onClick": lambda event: toggle_1()}),
        idom.html.input({"type": "checkbox", "onClick": lambda event: toggle_2()}),
        idom.html.pre(f"{input_1} AND {input_2} = {input_1 and input_2}"),
    )


def use_toggle():
    state, set_state = idom.hooks.use_state(False)

    def toggle_state():
        set_state(lambda old_state: not old_state)

    return state, toggle_state


idom.run(AndGate)
