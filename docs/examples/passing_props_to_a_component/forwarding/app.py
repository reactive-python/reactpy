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
def profile(**props):
    return html.div({"className": "card"}, avatar(**props))


@component
def app():
    return profile(
        person={"name": "Lin Lanying", "image_id": "1bX5QH6"},
        size=100,
    )
