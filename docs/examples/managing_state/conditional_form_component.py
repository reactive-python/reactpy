from reactpy import component, html


# start
@component
def error(status):
    if status == "error":
        return html.p(
            {"className": "error"}, "Good guess but a wrong answer. Try again!"
        )

    return ""


@component
def form(status="empty"):
    # Try "submitting", "error",  "success":
    if status == "success":
        return html.h1("That's right!")

    return html.fragment(
        html.h2("City quiz"),
        html.p(
            "In which city is there a billboard that turns air into drinkable water?"
        ),
        html.form(
            html.textarea({"disabled": "True" if status == "submitting" else "False"}),
            html.br(),
            html.button(
                {"disabled": (True if status in ["empty", "submitting"] else "False")},
                "Submit",
            ),
            error(status),
        ),
    )
