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
        html.label(
            "To: ",
            html.select(
                html.option("Alice", value="Alice"),
                html.option("Bob", value="Bob"),
                value=recipient,
                on_change=lambda event: set_recipient(event["target"]["value"]),
            ),
        ),
        html.input(
            type="text",
            placeholder="Your message...",
            value=message,
            on_change=lambda event: set_message(event["target"]["value"]),
        ),
        html.button("Send", type="submit"),
        on_submit=handle_submit,
        style={"display": "inline-grid"},
    )


run(App)
