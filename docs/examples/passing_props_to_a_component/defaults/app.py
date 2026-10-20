from reactpy import component, html

# start


def get_image_url(person, size="s"):
    return f"../../assets/images/demos/{person['image_id']}{size}.jpg"


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
def profile():
    return html.div(
        avatar(person={"name": "Lin Lanying", "image_id": "1bX5QH6"}),
        avatar(
            person={"name": "Katsuko Saruhashi", "image_id": "YfeOqp2"},
            size=200,
        ),
    )
