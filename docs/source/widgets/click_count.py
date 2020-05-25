import idom


@idom.element
async def ClickCount(self, count=0):
    async def increment(event):
        self.update(count=count + 1)

    return idom.html.button({"onClick": increment}, [f"Click count: {count}"])


display(ClickCount)
