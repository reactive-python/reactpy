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
        roots, new, old = await layout.render()
        msg = self._change_message(roots, new, old)
        await socket.send(json.dumps(msg))

    async def _recv(self, socket, layout):
        msg = json.loads(await socket.recv())
        await layout.apply(**msg["body"]["event"])

    def _change_message(self, roots, new, old):
        return {
            "header": {},
            "body": {
                "render": {
                    "new": new,
                    "old": old,
                    "roots": roots,
                }
            }
        }


class SimpleWebServer(SimpleServer):

    @handle("route", "/idom/client/<path:path>")
    async def client(self, request, path):
        return await response.file(os.path.join(STATIC, "simple-client", *path.split("\n")))
