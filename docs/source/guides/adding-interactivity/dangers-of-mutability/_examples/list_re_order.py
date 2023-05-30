from reactpy import component, html, run, use_state


@component
def ArtistList():
    artists, set_artists = use_state(
        ["Marta Colvin Andrade", "Lamidi Olonade Fakeye", "Louise Nevelson"]
    )

    def handle_sort_click(event):
        set_artists(sorted(artists))

    def handle_reverse_click(event):
        set_artists(list(reversed(artists)))

    return html.div(
        html.h1("Inspiring sculptors:"),
        html.button({"on_click": handle_sort_click}, "sort"),
        html.button({"on_click": handle_reverse_click}, "reverse"),
        html.ul([html.li({"key": name}, name) for name in artists]),
    )


run(ArtistList)
