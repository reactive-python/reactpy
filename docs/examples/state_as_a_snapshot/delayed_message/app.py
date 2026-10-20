import asyncio

from reactpy import component, html, use_state


# start
@component
def form():
    to, set_to = use_state("Alice")
    message, set_message = use_state("Hello")
    status, set_status = use_state("Not sent yet")

    async def handle_submit(event):
        # This handler closes over `to` and `message` from ITS OWN render.
        set_status("Sending...")
        await asyncio.sleep(5)
        set_status(f"You said {message} to {to}")

    async def handle_to_change(event):
        set_to(await event.target.value)

    async def handle_message_change(event):
        set_message(await event.target.value)

    return html.div(
        html.label(
            "To: ",
            html.input(
                {
                    "value": to,
                    "onChange": handle_to_change,
                }
            ),
        ),
        html.label(
            "Message: ",
            html.input(
                {
                    "value": message,
                    "onChange": handle_message_change,
                }
            ),
        ),
        html.button({"onClick": handle_submit}, "Send"),
        html.p(status),
    )
