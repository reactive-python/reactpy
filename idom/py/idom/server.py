import abc
import asyncio
import json
import jsonschema
import websockets


class BaseServer(abc.ABC):

    async def run(self, *args, **kwargs):
        return (await websockets.serve(self._run, *args, **kwargs))

    async def _run(self, socket, path):
        layout = self._make_layout()
        layout = Layout(self._root(*self._args, **self._kwargs))
        await self._handshake(socket, path, layout)
        sl = self._send_loop(socket, layout)
        rl = self._recv_loop(socket, layout)
        await asyncio.gather(sl, rl)

    async def _handshake(self, socket, path, layout):
        self._client_handshake(path, json.loads(await socket.recv()))
        await socket.send(json.dumps(self._server_handshake(layout)))

    async def _send_loop(self, socket, layout):
        while True:
            await layout.changed()
            change = await layout.render()
            msg = self._form_change_message(change)
            await socket.send(json.dumps(msg))

    async def _recv_loop(self, socket, layout):
        while True:
            msg = json.loads(await socket.recv())
            event = self._load_event_message(msg)
            await layout.handle(**event)

    @abc.abstractmethod
    def _make_layout(self):
        pass

    @abc.abstractmethod
    def _client_handshake(self, path, info):
        pass

    @abc.abstractmethod
    def _server_handshake(self, layout):
        pass

    @abc.abstractmethod
    def _make_change_message(self, change):
        pass

    @abc.abstractmethod
    def _load_event_message(self, msg):
        pass


class SimpleServer(BaseServer):

    def __init__(self, root, *args, **kwargs):
        self._root = root
        self._args = args
        self._kwargs = kwargs

    def _make_layout(self):
        return Layout(self._root(*self._args, **self._kwargs))

    def _client_handshake(self, path, info):
        pass

    def _server_handshake(self, shake, layout):
        return {"root": layout.root}

    def _make_change_message(self, change):
        return change

    def _load_event_message(self, event):
        return event
