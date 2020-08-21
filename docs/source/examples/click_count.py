import idom


@idom.element
async def ClickCount(self):
    count, set_count = idom.hook.use_state(0)

    async def increment(event):
        set_count(count + 1)

    return idom.html.button({"onClick": increment}, [f"Click count: {count}"])


display(ClickCount)
