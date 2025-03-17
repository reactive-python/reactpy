from reactpy import component, html


# start
@component
def picture():
    return html.div(
        {"className": "background background--active"},
        html.img(
            {
                "className": "picture",
                "alt": "Rainbow houses in Kampung Pelangi, Indonesia",
                "src": "https://i.imgur.com/5qwVYb1.jpeg",
            }
        ),
    )
