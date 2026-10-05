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

    return html.div(
        html.label(
            "To: ",
            html.input(
                {
                    "value": to,
                    "onChange": lambda event: set_to(event["target"]["value"]),
                }
            ),
        ),
        html.label(
            "Message: ",
            html.input(
                {
                    "value": message,
                    "onChange": lambda event: set_message(event["target"]["value"]),
                }
            ),
        ),
        html.button({"onClick": handle_submit}, "Send"),
        html.p(status),
    )
