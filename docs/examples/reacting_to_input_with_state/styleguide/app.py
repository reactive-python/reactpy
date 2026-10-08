from reactpy import component, html


# start
@component
def form(status="empty"):
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
            html.p({"className": "Error"}, "Good guess but a wrong answer. Try again!")
            if status == "error"
            else None,
        ),
    )


@component
def app():
    """Render every visual state at once -- a "living styleguide".

    Because the mock is driven by a prop, all five states can sit side by side
    in one page and be compared without clicking anything.
    """
    statuses = ["empty", "typing", "submitting", "success", "error"]
    return html.div(
        [
            html.section(
                {"key": status},
                html.h4(status),
                form(status=status),
            )
            for status in statuses
        ]
    )
