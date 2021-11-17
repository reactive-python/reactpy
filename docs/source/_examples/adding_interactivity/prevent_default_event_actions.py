from idom import component, event, html, run


@component
def DoNotChangePages():
    return html.div(
        html.p("Normally clicking this link would take you to a new page"),
        html.a(
            {
                "onClick": event(lambda event: None, prevent_default=True),
                "href": "https://google.com",
            },
            "https://google.com",
        ),
    )


run(DoNotChangePages)
