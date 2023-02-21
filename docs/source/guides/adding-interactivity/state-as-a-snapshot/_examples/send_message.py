from idom import component, event, html, run, use_state


@component
def App():
    is_sent, set_is_sent = use_state(False)
    message, set_message = use_state("")

    if is_sent:
        return html.div(
            html.h1("Message sent!"),
            html.button(
                {"on_click": lambda event: set_is_sent(False)}, "Send new message?"
            ),
        )

    @event(prevent_default=True)
    def handle_submit(event):
        set_message("")
        set_is_sent(True)

    return html.form(
        {"on_submit": handle_submit, "style": {"display": "inline-grid"}},
        html.textarea(
            {
                "placeholder": "Your message here...",
                "value": message,
                "on_change": lambda event: set_message(event["target"]["value"]),
            }
        ),
        html.button({"type": "submit"}, "Send"),
    )


run(App)
