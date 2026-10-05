from reactpy import component, html


@component
def profile():
    return html.img(
        {"src": "https://i.imgur.com/MK3eW3As.jpg", "alt": "Katherine Johnson"}
    )


@component
def gallery():
    return html.section(
        html.h1("Amazing scientists"),
        profile(),
        profile(),
        profile(),
    )
