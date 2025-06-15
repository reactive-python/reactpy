from reactpy import component, html


# start
@component
def form(status="empty"):
    if status == "success":
        return html.h1("That's right!")

    return html.fragment(
        html.h2("City quiz"),
        html.p(
            "In which city is there a billboard that turns air into drinkable water?"
        ),
        html.form(html.textarea(), html.br(), html.button("Submit")),
    )
