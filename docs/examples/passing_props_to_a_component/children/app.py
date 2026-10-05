from reactpy import component, html

# start


def get_image_url(person, size="s"):
    return f"https://i.imgur.com/{person['image_id']}{size}.jpg"


@component
def avatar(person, size=100):
    return html.img(
        {
            "className": "avatar",
            "src": get_image_url(person),
            "alt": person["name"],
            "width": size,
            "height": size,
        }
    )


@component
def card(*children):
    return html.div({"className": "card"}, *children)


@component
def profile():
    return card(
        avatar(person={"name": "Katsuko Saruhashi", "image_id": "YfeOqp2"}),
    )
