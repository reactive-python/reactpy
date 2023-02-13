from idom import component, html, run, use_state


@component
def ArtistList():
    artist_to_add, set_artist_to_add = use_state("")
    artists, set_artists = use_state([])

    def handle_change(event):
        set_artist_to_add(event["target"]["value"])

    def handle_click(event):
        if artist_to_add and artist_to_add not in artists:
            set_artists([*artists, artist_to_add])
            set_artist_to_add("")

    return html.div(
        html.h1("Inspiring sculptors:"),
        html.input({"value": artist_to_add, "onChange": handle_change}),
        html.button({"onClick": handle_click}, "add"),
        html.ul([html.li({"key": name}, name) for name in artists]),
    )


run(ArtistList)
