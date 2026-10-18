from reactpy import component, html


# start
@component
def form(status="empty"):
    """A mock: the visual states are driven by a prop, not by real logic.

    Rendering this with each status is the fastest way to enumerate the states
    before writing any interaction code.
    """
    if status == "success":
        return html.h1("That's right!")

    return html.div(
        html.h2("City quiz"),
        html.p(
            "In which city is there a billboard that turns air into drinkable water?"
        ),
        html.form(
            html.textarea({"disabled": status == "submitting"}),
            html.br(),
            html.button(
                {"disabled": status in {"empty", "submitting"}},
                "Submit",
            ),
            (
                html.p(
                    {"className": "Error"}, "Good guess but a wrong answer. Try again!"
                )
                if status == "error"
                else None
            ),
        ),
    )
