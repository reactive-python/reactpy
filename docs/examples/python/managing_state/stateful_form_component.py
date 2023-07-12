from reactpy import component, event, html, hooks
import asyncio


async def submit_form():
    await asyncio.wait(5)


# start
@component
def error_msg(error):
    if error:
        return html.p(
            {"class_name": "error"}, 
            "Good guess but a wrong answer. Try again!"
        )
    else:
        return ""
    

@component
def form(status="empty"):
    answer, set_answer = hooks.use_state("")
    error, set_error = hooks.use_state(None)
    status, set_status = hooks.use_state("typing")
    
    @event(prevent_default=True)
    async def handle_submit(event):
        set_status("submitting")
        try:
            await submit_form(answer)
            set_status("success")
        except Exception:
            set_status("typing")
            set_error(Exception)

    @event()
    def handle_textarea_change(event):
        set_answer(event["target"]["value"])
    
    if status == "success":
        return html.h1("That's right!")
    else:
        return html._(
            html.h2("City quiz"),
            html.p(
                "In which city is there a billboard \
                    that turns air into drinkable water?"
            ),
            html.form(
                {"on_submit": handle_submit},
                html.textarea(
                    {
                        "value": answer, 
                        "on_change": handle_textarea_change, 
                        "disabled": True if status == "submitting" else "False"
                    }
                ),
                html.br(),
                html.button(
                    {   
                        "disabled": True if status == "empty" 
                            or status == "submitting" else "False"
                    }, 
                     "Submit"
                ),
                error_msg(error)
            )
        )