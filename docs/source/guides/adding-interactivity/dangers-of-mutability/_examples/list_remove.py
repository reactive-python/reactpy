from idom import component, html, run, use_state


@component
def ArtistList():
    artist_to_add, set_artist_to_add = use_state("")
    artists, set_artists = use_state(
        ["Marta Colvin Andrade", "Lamidi Olonade Fakeye", "Louise Nevelson"]
    )

    def handle_change(event):
        set_artist_to_add(event["target"]["value"])

    def handle_add_click(event):
        if artist_to_add not in artists:
            set_artists([*artists, artist_to_add])
            set_artist_to_add("")

    def make_handle_delete_click(index):
        def handle_click(event):
            set_artists(artists[:index] + artists[index + 1 :])

        return handle_click

    return html.div(
        html.h1("Inspiring sculptors:"),
        html.input({"value": artist_to_add, "onChange": handle_change}),
        html.button({"onClick": handle_add_click}, "add"),
        html.ul(
            [
                html.li(
                    {"key": name},
                    name,
                    html.button({"onClick": make_handle_delete_click(index)}, "delete"),
                )
                for index, name in enumerate(artists)
            ]
        ),
    )


run(ArtistList)
