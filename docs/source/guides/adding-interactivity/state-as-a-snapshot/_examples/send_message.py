from reactpy import component, event, html, run, use_state


@component
def App():
    is_sent, set_is_sent = use_state(False)
    message, set_message = use_state("")

    async def handle_send_again(event):
        set_is_sent(False)

    async def handle_message_change(event):
        set_message(event["target"]["value"])

    if is_sent:
        return html.div(
            html.h1("Message sent!"),
            html.button({"on_click": handle_send_again}, "Send new message?"),
        )

    @event(prevent_default=True)
    async def handle_submit(event):
        set_message("")
        set_is_sent(True)

    return html.form(
        {"on_submit": handle_submit, "style": {"display": "inline-grid"}},
        html.textarea(
            {
                "placeholder": "Your message here...",
                "value": message,
                "on_change": handle_message_change,
            }
        ),
        html.button({"type": "submit"}, "Send"),
    )


run(App)
