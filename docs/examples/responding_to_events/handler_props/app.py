from reactpy import component, html, use_state


# start
@component
def button(on_click, *children):
    return html.button({"onClick": on_click}, *children)


@component
def play_button(movie_name):
    shown, set_shown = use_state("")

    def handle_play_click(event):
        set_shown(f"Playing {movie_name}!")

    return html.div(
        button(handle_play_click, f'Play "{movie_name}"'),
        html.p(shown),
    )


@component
def upload_button():
    shown, set_shown = use_state("")

    def handle_upload_click(event):
        set_shown("Uploading!")

    return html.div(
        button(handle_upload_click, "Upload Image"),
        html.p(shown),
    )


@component
def toolbar():
    return html.div(play_button("Kiki's Delivery Service"), upload_button())
