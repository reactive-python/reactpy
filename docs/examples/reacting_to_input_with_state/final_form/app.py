import asyncio

from reactpy import component, html, use_state


async def submit_form(answer):
    """Pretend to hit the network; only "Lima" is correct."""
    await asyncio.sleep(1.5)
    if answer.lower() != "lima":
        msg = "Good guess but a wrong answer. Try again!"
        raise ValueError(msg)


# start
@component
def form():
    answer, set_answer = use_state("")
    error, set_error = use_state("")
    status, set_status = use_state("typing")  # 'typing', 'submitting', or 'success'

    if status == "success":
        return html.h1("That's right!")

    async def handle_submit(event):
        # Awaiting inside the handler is fine: ReactPy still submits the form's
        # defaults because it detects preventDefault() from the handler's code,
        # not from when it runs.
        event.preventDefault()
        set_status("submitting")
        try:
            await submit_form(answer)
        except ValueError as exc:
            set_status("typing")
            set_error(str(exc))
        else:
            set_status("success")

    def handle_textarea_change(event):
        set_answer(event["target"]["value"])

    return html.div(
        html.h2("City quiz"),
        html.p(
            "In which city is there a billboard that turns air into drinkable water?"
        ),
        html.form(
            {"onSubmit": handle_submit},
            html.textarea(
                {
                    "value": answer,
                    "onChange": handle_textarea_change,
                    "disabled": status == "submitting",
                }
            ),
            html.br(),
            html.button(
                {
                    "disabled": len(answer) == 0 or status == "submitting",
                    "type": "submit",
                },
                "Submit",
            ),
            html.p({"className": "Error"}, error) if error else None,
        ),
    )
