from reactpy import component, html, use_state


def initial_artworks():
    return [
        {
            "id": 0,
            "title": "The Day of the Ribbon",
            "artist": "Eva Gonzalès",
            "seen": False,
        },
        {
            "id": 1,
            "title": "A loge at the Folies-Bergère",
            "artist": "Édouard Manet",
            "seen": False,
        },
    ]


# start
@component
def form():
    artworks, set_artworks = use_state(initial_artworks())

    def handle_toggle(id_to_toggle):
        async def handler(event):
            # Copy the LIST, and copy the one dict inside it that changed.
            # A shallow copy would leave the dict shared with the old state.
            set_artworks(
                [
                    (
                        {**artwork, "seen": not artwork["seen"]}
                        if artwork["id"] == id_to_toggle
                        else artwork
                    )
                    for artwork in artworks
                ]
            )

        return handler

    return html.ul(
        [
            html.li(
                {"key": artwork["id"]},
                html.label(
                    html.input(
                        {
                            "type": "checkbox",
                            "checked": artwork["seen"],
                            "onChange": handle_toggle(artwork["id"]),
                        }
                    ),
                    f"{artwork['title']} - {artwork['artist']}",
                ),
            )
            for artwork in artworks
        ]
    )
