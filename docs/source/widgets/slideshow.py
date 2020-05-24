import idom


@idom.element
async def Slideshow(self, index=0):
    async def next_image(event):
        self.update(index + 1)

    url = f"https://picsum.photos/800/300?image={index}"
    return idom.html.img({"src": url, "onClick": next_image})


display(Slideshow)
