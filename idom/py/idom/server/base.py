import abc
import asyncio
import json
from multiprocessing import Process
from sanic import Sanic
from sanic_cors import CORS


def handle(*args, **kwargs):
    def setup(function):
        handle = Handle(*args, **kwargs)
        return handle.with_method(function)
    return setup


class Handle:

    __slots__ = ("_kind", "_args", "_kwargs", "_function", "_name")

    def __init__(self, kind, *args, **kwargs):
        self._kind = kind
        self._args = args
        self._kwargs = kwargs
        self._function = None

    def __set_name__(self, cls, name):
        cls._handles += (name,)
        self._name = name

    def setup(self, obj, app):
        if self._function is not None:
            method = getattr(obj, self._name)
            getattr(app, self._kind)(*self._args, **self._kwargs)(method)
        else:
            getattr(app, self._kind)(*self._args, **self._kwargs)

    def with_method(self, function):
        self._function = function
        return self

    def __get__(self, obj, cls):
        if obj is None or self._function is None:
            return self
        else:
            return self._function.__get__(obj, cls)


class BaseServer(abc.ABC):

    _handles = ()

    def run(self, *args, cors=False, **kwargs):
        app = self._app = Sanic()
        if cors:
            CORS(app)
        for h in self._handles:
            handle = getattr(type(self), h)
            handle.setup(self, app)
        self._app.run(*args, **kwargs)

    def daemon(self, *args, **kwargs):
        return Process(
            target=self.run,
            args=args,
            kwargs=kwargs,
            daemon=True,
        ).start()

    @handle("websocket", "/stream")
    async def _stream(self, request, socket):
        layout = self._make_layout()
        await asyncio.gather(
            self._send_loop(socket, layout),
            self._recv_loop(socket, layout)
        )

    async def _send_loop(self, socket, layout):
        while True:
            await layout.changed()
            msg = await self._form_change_message(layout)
            await socket.send(json.dumps(msg))

    async def _recv_loop(self, socket, layout):
        while True:
            msg = json.loads(await socket.recv())
            await self._load_event_message(layout, msg)

    @abc.abstractmethod
    def _make_layout(self):
        pass

    @abc.abstractmethod
    def _form_change_message(self, change):
        pass

    @abc.abstractmethod
    def _load_event_message(self, msg):
        pass
