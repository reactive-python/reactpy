from reactpy import component, html, use_state


# start
@component
def panel(title, is_active, on_show, *children):
    return html.section(
        {"className": "panel"},
        html.h3(title),
        (html.p(*children) if is_active else html.button({"onClick": on_show}, "Show")),
    )


@component
def accordion():
    active_index, set_active_index = use_state(0)

    return html(
        html.h2("Almaty, Kazakhstan"),
        panel(
            "About",
            active_index == 0,
            lambda event: set_active_index(0),
            "With a population of about 2 million, Almaty is Kazakhstan's "
            "largest city. From 1929 to 1997, it was its capital city.",
        ),
        panel(
            "Etymology",
            active_index == 1,
            lambda event: set_active_index(1),
            "The name comes from алма, the Kazakh word for “apple” and is "
            "often translated as “full of apples”.",
        ),
    )
