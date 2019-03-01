import abc
import sanic
import asyncio
from websockets import WebSocketCommonProtocol
from multiprocessing import Process
from sanic import Sanic
from sanic_cors import CORS

from typing import Any, Callable, Tuple

from idom import Layout


def handle(*args: Any, **kwargs: Any) -> Callable:
    def setup(function: Callable) -> "Handle":
        handle = Handle(*args, **kwargs)
        return handle.with_method(function)

    return setup


class Handle:

    __slots__ = ("_kind", "_args", "_kwargs", "_function", "_name")

    def __init__(self, kind: str, *args: Any, **kwargs: Any):
        self._kind = kind
        self._args = args
        self._kwargs = kwargs
        self._function = None

    def __set_name__(self, cls, name):
        cls._handles += (name,)
        self._name = name

    def setup(self, obj: "BaseServer", app: Sanic):
        if self._function is not None:
            method = getattr(obj, self._name)
            getattr(app, self._kind)(*self._args, **self._kwargs)(method)
        else:
            getattr(app, self._kind)(*self._args, **self._kwargs)

    def with_method(self, function) -> "Handle":
        self._function = function
        return self

    def __get__(self, obj, cls):
        if obj is None or self._function is None:
            return self
        else:
            return self._function.__get__(obj, cls)


class BaseServer(abc.ABC):

    _handles: Tuple[str, ...] = ()

    def run(self, *args: Any, cors: bool = False, **kwargs: Any):
        app = self._app = Sanic()
        if cors:
            CORS(app)
        for h in self._handles:
            handle = getattr(type(self), h)
            handle.setup(self, app)
        self._app.run(*args, **kwargs)

    def daemon(self, *args: Any, **kwargs: Any):
        return Process(target=self.run, args=args, kwargs=kwargs, daemon=True).start()

    @handle("websocket", "/idom/stream")
    async def _stream(
        self, request: sanic.request.Request, socket: WebSocketCommonProtocol
    ):
        layout = self._init_layout()
        await asyncio.gather(
            self._send_loop(socket, layout), self._recv_loop(socket, layout)
        )

    async def _send_loop(self, socket: WebSocketCommonProtocol, layout: Layout):
        while True:
            await self._send(socket, layout)

    async def _recv_loop(self, socket: WebSocketCommonProtocol, layout: Layout):
        while True:
            await self._recv(socket, layout)

    @abc.abstractmethod
    def _init_layout(self):
        ...

    @abc.abstractmethod
    def _send(self, socket: WebSocketCommonProtocol, layout: Layout):
        ...

    @abc.abstractmethod
    def _recv(self, socket: WebSocketCommonProtocol, layout: Layout):
        ...
