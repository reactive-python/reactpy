import idom
from idom.server.sanic import PerClientStateServer

colors = ["red", "blue", "purple", "green", "orange", "yellow"]


@idom.element
async def ColorGrid():
    return idom.html.div([ColorRow(0) for i in range(100)])


@idom.element
async def ColorRow(count):
    count, set_count = idom.hooks.use_state(count)

    def shift():
        set_count(count + 1)

    return idom.html.div(
        {"style": {"height": "20px"}},
        [ColorRowItem(count, i, shift) for i in range(200)],
    )


@idom.element
async def ColorRowItem(count, index, shift):
    async def tick(event):
        shift()

    return idom.html.div(
        {
            "onClick": tick,
            "style": {
                "backgroundColor": colors[(count + index) % len(colors)],
                "height": "20px",
                "width": "20px",
                "float": "left",
            },
        }
    )


PerClientStateServer(ColorGrid).run("localhost", 8765)
