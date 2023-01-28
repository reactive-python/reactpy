from idom import component, event, html, run, use_state


@component
def App():
    is_sent, set_is_sent = use_state(False)
    message, set_message = use_state("")

    if is_sent:
        return html.div(
            html.h1("Message sent!"),
            html.button("Send new message?", on_click=lambda event: set_is_sent(False)),
        )

    @event(prevent_default=True)
    def handle_submit(event):
        set_message("")
        set_is_sent(True)

    return html.form(
        html.textarea(
            placeholder="Your message here...",
            value=message,
            on_change=lambda event: set_message(event["target"]["value"]),
        ),
        html.button("Send", type="submit"),
        on_submit=handle_submit,
        style={"display": "inline-grid"},
    )


run(App)
