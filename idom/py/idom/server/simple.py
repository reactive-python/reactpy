import os
import json
import pprint
from sanic import response

from idom.layout import Layout
from idom.utils import STATIC

from .base import BaseServer, handle


class SimpleServer(BaseServer):

    def __init__(self, element, *args, **kwargs):
        self._element = element
        self._args = args
        self._kwargs = kwargs

    def _init_layout(self):
        return Layout(self._element(*self._args, **self._kwargs))

    async def _send(self, socket, layout):
        await layout.changed()
        updates, change = await layout.render()
        msg = self._change_message(layout.root, updates, change)
        await socket.send(json.dumps(msg))

    async def _recv(self, socket, layout):
        msg = json.loads(await socket.recv())
        await layout.handle(**msg["body"]["event"])

    def _change_message(self, root, updates, change):
        return {
            "header": {"root": root},
            "body": {
                "models": change,
                "updateRoots": updates,
            }
        }


class SimpleWebServer(SimpleServer):

    @handle("route", "/idom/client/<path:path>")
    async def client(self, request, path):
        print(path)
        return await response.file(os.path.join(STATIC, "simple-client", *path.split("\n")))
