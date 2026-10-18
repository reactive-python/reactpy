from reactpy import component, html, use_state


@component
def counter():
    count, set_count = use_state(0)

    async def handle_count_click(event):
        set_count(count + 1)

    return html.div(
        html.h1(count),
        html.button({"onClick": handle_count_click}, "Add 1"),
    )


@component
def badge():
    # The tag's `class` argument styles the mount element, not this markup, so
    # the component is free to render whatever it likes inside it.
    return html.div(
        html.span({"class": "badge-label"}, "Status:"),
        html.span({"class": "badge-value"}, "active"),
    )
