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
                "className": "avatar",
                "src": user["image_url"],
                "alt": f"Photo of {user['name']}",
                "style": {
                    "width": user["image_size"],
                    "height": user["image_size"],
                },
            }
        ),
    )
