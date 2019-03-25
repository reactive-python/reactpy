import os
import json
from sanic import response, request, Blueprint
from websockets import WebSocketCommonProtocol

from typing import List, Dict, Any

from idom.layout import Layout
from idom.utils import STATIC

from .base import BaseServer, handle


class SimpleServer(BaseServer):
    def __init__(self, element, *args, **kwargs):
        super().__init__()
        self._element = element
        self._args = args
        self._kwargs = kwargs
        self.blueprint(Blueprint("idom", url_prefix="/idom"))

    def _init_layout(self):
        return Layout(self._element(*self._args, **self._kwargs))

    async def _send(self, socket: WebSocketCommonProtocol, layout: Layout):
        roots, new, old = await layout.render()
        msg = self._change_message(roots, new, old)
        await socket.send(json.dumps(msg))

    async def _recv(self, socket: WebSocketCommonProtocol, layout: Layout):
        msg = json.loads(await socket.recv())
        await layout.apply(**msg["body"]["event"])

    def _change_message(
        self, roots: List[str], new: Dict[str, Dict], old: List[str]
    ) -> Dict[str, Any]:
        return {
            "header": {},
            "body": {"render": {"new": new, "old": old, "roots": roots}},
        }


class SimpleWebServer(SimpleServer):
    @handle("idom", "route", "/client/<path:path>")
    async def client(self, request: request.Request, path: str):
        return await response.file(
            os.path.join(STATIC, "simple-client", *path.split("\n"))
        )
