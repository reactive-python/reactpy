from reactpy import component, html


# Do not do this: a component defined inside another component.
@component
def gallery():
    @component
    def profile():
        return html.img({"src": "https://i.imgur.com/MK3eW3As.jpg"})

    return html.section(
        html.h1("Amazing scientists"),
        profile(),
        profile(),
        profile(),
    )
