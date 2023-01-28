from idom import component, hooks, html, run


@component
def SyncedInputs():
    value, set_value = hooks.use_state("")
    return html.p(
        Input("First input", value, set_value),
        Input("Second input", value, set_value),
    )


@component
def Input(label, value, set_value):
    def handle_change(event):
        set_value(event["target"]["value"])

    return html.label(label + " ", html.input(value=value, on_change=handle_change))


run(SyncedInputs)
