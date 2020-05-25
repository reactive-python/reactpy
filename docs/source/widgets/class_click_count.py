import idom
from idom.core import AbstractElement


class ClickCount(AbstractElement):

    __slots__ = ["_count"]

    def __init__(self):
        super().__init__()
        self._count = 0

    async def render(self):
        async def increment(event):
            self._count += 1
            self.update()

        return idom.html.button(
            {"onClick": increment}, [f"You clicked {self._count} times"],
        )


display(ClickCount)
