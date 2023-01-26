import idom


@idom.component
def Slideshow():
    index, set_index = idom.hooks.use_state(0)

    def next_image(event):
        set_index(index + 1)

    return idom.html.img(
        src=f"https://picsum.photos/id/{index}/800/300",
        style={"cursor": "pointer"},
        on_click=next_image,
    )


idom.run(Slideshow)
