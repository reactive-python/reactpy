import idom


@idom.component
def DoNotChangePages():
    return idom.html.div(
        idom.html.p("Normally clicking this link would take you to a new page"),
        idom.html.a(
            {
                "onClick": idom.event(lambda e: None, prevent_default=True),
                "href": "https://google.com",
            },
            "https://google.com",
        ),
    )


idom.run(DoNotChangePages)
