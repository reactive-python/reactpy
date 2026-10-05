from reactpy import component, html


# start
@component
def profile():
    return html.img(
        {"src": "https://i.imgur.com/MK3eW3Am.jpg", "alt": "Katherine Johnson"}
    )
