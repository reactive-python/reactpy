from reactpy import component, html, use_state


# start
@component
def panel(title, *children):
    is_active, set_is_active = use_state(False)

    return html.section(
        {"className": "panel"},
        html.h3(title),
        html.p(*children)
        if is_active
        else html.button({"onClick": lambda event: set_is_active(True)}, "Show"),
    )


@component
def accordion():
    return html(
        html.h2("Almaty, Kazakhstan"),
        panel(
            "About",
            "With a population of about 2 million, Almaty is Kazakhstan's "
            "largest city. From 1929 to 1997, it was its capital city.",
        ),
        panel(
            "Etymology",
            "The name comes from алма, the Kazakh word for “apple” and is "
            "often translated as “full of apples”.",
        ),
    )
