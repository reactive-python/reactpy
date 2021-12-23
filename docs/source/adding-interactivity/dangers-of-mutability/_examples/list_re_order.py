from idom import component, html, run, use_state


@component
def ArtistList():
    artists, set_artists = use_state(
        ["Marta Colvin Andrade", "Lamidi Olonade Fakeye", "Louise Nevelson"]
    )

    def handle_sort_click(event):
        set(list(sorted(set_artists)))

    def handle_reverse_click(event):
        set(list(reversed(set_artists)))

    return html.div(
        html.h1("Inspiring sculptors:"),
        html.button({"onClick": handle_sort_click}, "sort"),
        html.button({"onClick": handle_reverse_click}, "reverse"),
        html.ul([html.li(name, key=name) for name in artists]),
    )


run(ArtistList)
