from idom import component, html, run


@component
def Button(display_text, on_click):
    return html.button(display_text, on_click=on_click)


@component
def PlayButton(movie_name):
    def handle_click(event):
        print(f"Playing {movie_name}")

    return Button(f"Play {movie_name}", on_click=handle_click)


@component
def FastForwardButton():
    def handle_click(event):
        print("Skipping ahead")

    return Button("Fast forward", on_click=handle_click)


@component
def App():
    return html.div(
        PlayButton("Buena Vista Social Club"),
        FastForwardButton(),
    )


run(App)
