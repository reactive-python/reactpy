import reactpy


@reactpy.component
def Slideshow():
    index, set_index = reactpy.hooks.use_state(0)

    def next_image(event):
        set_index(index + 1)

    return reactpy.html.img(
        {
            "src": f"https://picsum.photos/id/{index}/800/300",
            "style": {"cursor": "pointer"},
            "on_click": next_image,
        }
    )


reactpy.run(Slideshow)
