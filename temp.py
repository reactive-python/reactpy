from idom import component, event, html, run


@component
def Form():
    @event(prevent_default=True)
    def handle_form(event):
        print(event["target"]["elements"])

    return html.form(
        {"onSubmit": handle_form},
        html.input({"name": "firstname"}),
        html.p("test"),
        html.button({"type": "submit", "value": "Submit"}, "Submit"),
        html.input({"lastname": "lastname"}),
        html.p("tes2t"),
    )


run(Form)
