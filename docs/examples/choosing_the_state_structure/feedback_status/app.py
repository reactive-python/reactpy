"""One status variable: the impossible combination is unrepresentable."""

import asyncio

from reactpy import component, html, use_state

DELAYS = {"slow": 0.25, "instant": 0}


# start
@component
def feedback(speed="slow"):
    text, set_text = use_state("")
    status, set_status = use_state("typing")

    async def submit(event):
        set_status("sending")
        await asyncio.sleep(DELAYS[speed])
        set_status("sent")

    # Plain names, not state: they cannot drift apart because they are derived.
    is_sending = status == "sending"
    is_sent = status == "sent"

    if is_sent:
        return html.div(html.h3("Thanks for your feedback!"))

    async def handle_text_change(event):
        set_text(await event.target.value)

    return html.div(
        html.p("How was your stay at The Prancing Pony?"),
        html.textarea(
            {
                "value": text,
                "onChange": handle_text_change,
                "disabled": is_sending,
            }
        ),
        html.br(),
        html.button({"onClick": submit, "disabled": is_sending}, "Send"),
        (html.p("Sending...") if is_sending else None),
        html.p({"id": "flags"}, f"status={status}"),
    )


@component
def app():
    return html.div(html.h3("One status"), feedback())
