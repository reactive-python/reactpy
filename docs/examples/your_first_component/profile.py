from reactpy import component, html

# start


@component
def profile():
    return html.img(
        {"src": "../../assets/images/demos/MK3eW3Am.jpg", "alt": "Katherine Johnson"}
    )
