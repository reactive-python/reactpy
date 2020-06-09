import idom


@idom.element
async def Slideshow(self, index=0):
    async def next_image(event):
        self.update(index + 1)

    return idom.html.img(
        {
            "src": f"https://picsum.photos/800/300?image={index}",
            "style": {"cursor": "pointer"},
            "onClick": next_image,
        }
    )


display(Slideshow)
