import asyncio

from idom import component, event, html, run, use_state


@component
def App():
    recipient, set_recipient = use_state("Alice")
    message, set_message = use_state("")

    @event(prevent_default=True)
    async def handle_submit(event):
        set_message("")
        print("About to send message...")
        await asyncio.sleep(5)
        print(f"Sent '{message}' to {recipient}")

    return html.form(
        {"onSubmit": handle_submit, "style": {"display": "inline-grid"}},
        html.label(
            "To: ",
            html.select(
                {
                    "value": recipient,
                    "onChange": lambda event: set_recipient(event["target"]["value"]),
                },
                html.option({"value": "Alice"}, "Alice"),
                html.option({"value": "Bob"}, "Bob"),
            ),
        ),
        html.input(
            {
                "type": "text",
                "placeholder": "Your message...",
                "value": message,
                "onChange": lambda event: set_message(event["target"]["value"]),
            }
        ),
        html.button({"type": "submit"}, "Send"),
    )


run(App)
