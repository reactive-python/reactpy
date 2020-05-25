import idom


@idom.element
async def Main(self):
    """We need this so the ClickHistory element gets a new list each time its viewed"""
    return ClickHistory([])


@idom.element(state="event_list")
async def ClickHistory(self, event_list):
    async def save_event(event):
        event_list.append(event)
        self.update()

    return idom.html.div(
        idom.html.button({"onClick": save_event}, ["Click me!"]),
        idom.html.pre(
            {"style": {"white-space": "pre-wrap"}},
            "\n".join(str(e) for e in event_list),
        ),
    )


display(Main)
