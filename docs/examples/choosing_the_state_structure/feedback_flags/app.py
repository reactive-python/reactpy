"""Two boolean flags that are free to contradict each other.

Press "Send (buggy)" to land in the state the second bullet describes: the send
finished, but is_sending was never cleared, so the screen says both.
"""

import asyncio

from reactpy import component, html, use_state

DELAY = 0.25


# start
@component
def feedback():
    text, set_text = use_state("")
    is_sending, set_is_sending = use_state(False)
    is_sent, set_is_sent = use_state(False)

    async def submit(event):
        set_is_sending(True)
        await asyncio.sleep(DELAY)
        # Forget either line below and the two flags disagree forever.
        set_is_sending(False)
        set_is_sent(True)

    async def submit_with_bug(event):
        set_is_sending(True)
        await asyncio.sleep(DELAY)
        set_is_sent(True)  # set_is_sending(False) was never called

    if is_sent:
        return html.div(
            html.h3("Thanks for your feedback!"),
            html.p({"id": "flags"}, f"is_sending={is_sending}  is_sent={is_sent}"),
        )

    return html.div(
        html.p("How was your stay at The Prancing Pony?"),
        html.textarea(
            {
                "value": text,
                "onChange": lambda event: set_text(event["target"]["value"]),
                "disabled": is_sending,
            }
        ),
        html.br(),
        html.button({"onClick": submit, "disabled": is_sending}, "Send"),
        html.button(
            {"onClick": submit_with_bug, "disabled": is_sending}, "Send (buggy)"
        ),
        (html.p("Sending...") if is_sending else None),
        html.p({"id": "flags"}, f"is_sending={is_sending}  is_sent={is_sent}"),
    )


@component
def app():
    return html.div(html.h3("Two flags"), feedback())
