from reactpy import component, html


# start
@component
def picture():
    return html.div(
        {"class_name": "background background--active"},
        html.img(
            {
                "class_name": "picture",
                "alt": "Rainbow houses in Kampung Pelangi, Indonesia",
                "src": "https://i.imgur.com/5qwVYb1.jpeg",
            }
        ),
    )
