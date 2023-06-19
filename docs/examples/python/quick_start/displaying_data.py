from reactpy import component, html

user = {
    "name": "Hedy Lamarr",
    "image_url": "https://i.imgur.com/yXOvdOSs.jpg",
    "image_size": 90,
}


@component
def profile():
    return html.div(
        html.h3(user["name"]),
        html.img(
            {
                "class_name": "avatar",
                "src": user["image_url"],
                "alt": f"Photo of {user['name']}",
                "style": {
                    "width": user["image_size"],
                    "height": user["image_size"],
                },
            }
        ),
    )


# end
if __name__ == "__main__":
    from reactpy import run
    from reactpy.utils import _read_docs_css

    @component
    def styled_app():
        return html._(html.style(_read_docs_css()), profile())

    run(styled_app)
