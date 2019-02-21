from idom.layout import Layout

from .base import BaseServer


class SimpleServer(BaseServer):

    def __init__(self, root, *args, **kwargs):
        self._root = root
        self._args = args
        self._kwargs = kwargs

    def _make_layout(self):
        return Layout(self._root(*self._args, **self._kwargs))

    async def _form_change_message(self, layout):
        change = await layout.render()
        return {
            "header": {"root": layout.root},
            "body": {"models": change}
        }

    async def _load_event_message(self, layout, message):
        await layout.handle(**message["body"]["event"])
