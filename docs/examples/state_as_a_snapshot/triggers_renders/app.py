from reactpy import component, html, use_state


# start
@component
def form():
    is_sent, set_is_sent = use_state(False)
    message, set_message = use_state("Hi!")

    if is_sent:
        return html.h1("Your message is on its way!")

    def handle_submit(event):
        event.preventDefault()
        set_is_sent(True)
        send_message(message)

    return html.form(
        {"onSubmit": handle_submit},
        html.textarea(
            {
                "placeholder": "Message",
                "value": message,
                "onChange": lambda event: set_message(event["target"]["value"]),
            }
        ),
        html.button({"type": "submit"}, "Send"),
    )


def send_message(message):
    print(f"Sending: {message}")
