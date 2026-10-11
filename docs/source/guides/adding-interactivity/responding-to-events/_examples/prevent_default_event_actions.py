from reactpy import component, event, html, run


@component
def DoNotChangePages():
    async def do_nothing(event):
        # the body is irrelevant here - 'prevent_default' does all the work
        ...

    return html.div(
        html.p("Normally clicking this link would take you to a new page"),
        html.a(
            {
                "on_click": event(do_nothing, prevent_default=True),
                "href": "https://google.com",
            },
            "https://google.com",
        ),
    )


run(DoNotChangePages)
