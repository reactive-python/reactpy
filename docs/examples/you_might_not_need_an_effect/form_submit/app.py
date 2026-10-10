"""Submit on the click, not from an Effect watching a piece of state."""

from data import send_email

from reactpy import component, html, use_state


# start
@component
def signup():
    email, set_email = use_state("")
    status, set_status = use_state("idle")

    async def handle_submit(event):
        event.preventDefault()
        # Wrong: set a "pending" flag and let an Effect notice it. That costs
        # a state variable, a render, and a way to submit the same value twice.
        #     set_pending(True)
        #
        # Right: do the work from the handler. It runs once per submission.
        set_status("sending...")
        await send_email(email)
        set_status(f"sent to {email}")

    return html.div(
        html.p(status),
        html.form(
            {"onSubmit": handle_submit},
            html.input(
                {
                    "value": email,
                    "placeholder": "you@example.com",
                    "onChange": lambda event: set_email(event["target"]["value"]),
                }
            ),
            html.button({"type": "submit"}, "Sign up"),
        ),
    )
