from idom import component, html, run, use_state


@component
def ArtistList():
    artists, set_artists = use_state(
        ["Marta Colvin Andrade", "Lamidi Olonade Fakeye", "Louise Nevelson"]
    )

    def handle_sort_click(event):
        set_artists(list(sorted(artists)))

    def handle_reverse_click(event):
        set_artists(list(reversed(artists)))

    return html.div(
        html.h1("Inspiring sculptors:"),
        html.button("sort", on_click=handle_sort_click),
        html.button("reverse", on_click=handle_reverse_click),
        html.ul([html.li(name, key=name) for name in artists]),
    )


run(ArtistList)
