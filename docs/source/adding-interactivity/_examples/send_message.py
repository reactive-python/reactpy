from idom import component, event, html, run, use_state


@component
def App():
    is_sent, set_is_sent = use_state(False)
    message, set_message = use_state("")

    if is_sent:
        return html.div(
            html.h1("Message sent!"),
            html.button(
                {"onClick": lambda event: set_is_sent(False)}, "Send new message?"
            ),
        )

    @event(prevent_default=True)
    def handle_submit(event):
        set_message("")
        set_is_sent(True)

    return html.form(
        {"onSubmit": handle_submit, "style": {"display": "inline-grid"}},
        html.textarea(
            {
                "placeholder": "Your message here...",
                "value": message,
                "onChange": lambda event: set_message(event["value"]),
            }
        ),
        html.button({"type": "submit"}, "Send"),
    )


run(App)
