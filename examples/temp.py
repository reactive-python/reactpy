import idom
from idom.server.sanic import PerClientStateServer


@idom.element
async def Slideshow():
    index, set_index = idom.hooks.use_state(0)

    @idom.event(target_id="test")
    async def next_image(event):
        set_index(index + 1)

    return idom.html.img(
        {
            "src": f"https://picsum.photos/800/300?image={index}",
            "style": {"cursor": "pointer"},
            "onClick": next_image,
        }
    )


PerClientStateServer(Slideshow).run("localhost", 8765)
