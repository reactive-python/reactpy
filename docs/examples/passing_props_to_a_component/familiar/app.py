from reactpy import component, html

# start


@component
def avatar():
    return html.img(
        {
            "className": "avatar",
            "src": "../../assets/images/demos/1bX5QH6.jpg",
            "alt": "Lin Lanying",
            "width": 100,
            "height": 100,
        }
    )


@component
def profile():
    return avatar()


@component
def app():
    return profile()
