import abc
import sanic
import asyncio
from functools import partial, wraps
from websockets import WebSocketCommonProtocol
from multiprocessing import Process
from sanic import Sanic, Blueprint
from sanic_cors import CORS

from typing import Any, Callable, Tuple, Dict

from idom import Layout


def handle(*args: Any, **kwargs: Any) -> Callable:
    def setup(function: Callable) -> "Handle":
        handle = Handle(*args, **kwargs)
        return handle.with_method(function)

    return setup


class Handle:

    __slots__ = ("_blueprint", "_kind", "_args", "_kwargs", "_function", "_name")

    def __init__(self, blueprint: str, kind: str, *args: Any, **kwargs: Any):
        self._blueprint = blueprint
        self._kind = kind
        self._args = args
        self._kwargs = kwargs
        self._function = None

    def __set_name__(self, cls, name):
        cls._handles += (name,)
        self._name = name

    def setup(self, obj: "BaseServer", app):
        blueprint = app.blueprints[self._blueprint]
        if self._function is not None:
            method = wraps(self._function)(partial(self._function, obj))
            getattr(blueprint, self._kind)(*self._args, **self._kwargs)(method)
        else:
            getattr(blueprint, self._kind)(*self._args, **self._kwargs)

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

    def __init__(self):
        self.app = Sanic()
        self._blueprints: List[Blueprint] = []

    def blueprint(self, bp: Blueprint):
        self._blueprints.append(bp)
        self.app.blueprint(bp)

    def run(self, *args: Any, cors: bool = False, **kwargs: Any):
        if "idom" not in self.app.blueprints:
            raise RuntimeError("The application must have a blueprint named 'idom'")
        if cors:
            CORS(app)
        for h in self._handles:
            handle = getattr(type(self), h)
            handle.setup(self, self.app)
        # we have to reregister them since we changed the blueprints
        for bp in self._blueprints:
            self.app.blueprint(bp)
        self.app.run(*args, **kwargs)

    def daemon(self, *args: Any, **kwargs: Any):
        proc = Process(target=self.run, args=args, kwargs=kwargs, daemon=True)
        proc.start()
        return proc

    @handle("idom", "websocket", "/stream")
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
