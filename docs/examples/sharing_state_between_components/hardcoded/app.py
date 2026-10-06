from reactpy import component, html


# start
@component
def panel(title, is_active, *children):
    return html.section(
        {"className": "panel"},
        html.h3(title),
        html.p(*children) if is_active else html.button("Show"),
    )


@component
def accordion():
    return html(
        html.h2("Almaty, Kazakhstan"),
        panel("About", True, "With a population of about 2 million..."),
        panel("Etymology", True, "The name comes from алма..."),
    )
