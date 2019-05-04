import asyncio
import json
import os
from sanic import Sanic, request, response
from threading import Thread
import uuid
from websockets import WebSocketCommonProtocol

from typing import TypeVar, Any, Dict

from .element import ElementConstructor
from .layout import Layout
from .render import SingleStateRenderer, SharedStateRenderer
from .utils import STATIC_DIRECTORY


ServerSelf = TypeVar("ServerSelf", bound="AbstractServer")


class AbstractServer:
    def __init__(self) -> None:
        self.app = Sanic()
        self._handlers = {"route:_client": {"uri": "/client/<path:path>"}}
        self._config = {"idom_url_prefix": "/idom"}

    def configure(self: ServerSelf, **config: Any) -> ServerSelf:
        for k, v in config.items():
            if k not in self._config:
                raise ValueError(f"Unknown configuration option {k!r}")
            else:
                self._config[k] = v
        return self

    def run(self, *args: Any, **kwargs: Any) -> None:
        self._setup_application()
        self.app.run(*args, **kwargs)

    def daemon(self, *args: Any, **kwargs: Any) -> Thread:
        def run() -> None:
            self._setup_application()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            server = self.app.create_server(*args, **kwargs)
            asyncio.ensure_future(server)
            loop.run_forever()

        thread = Thread(target=run)
        thread.start()
        return thread

    def _setup_application(self) -> None:
        idom_url_prefix = self._config["idom_url_prefix"]
        for key, params in self._handlers.items():
            route_type, method = key.split(":")
            if "uri" in params:
                params["uri"] = idom_url_prefix + params["uri"]
            getattr(self.app, route_type)(**params)(getattr(self, method))

    async def _client(
        self, request: request.Request, path: str
    ) -> response.HTTPResponse:
        return await response.file(
            os.path.join(STATIC_DIRECTORY, "simple-client", *path.split("\n"))
        )


class SimpleServer(AbstractServer):
    def __init__(
        self, element_constructor: ElementConstructor, *args: Any, **kwargs: Any
    ):
        super().__init__()
        self._element_constructor = element_constructor
        self._element_args = args
        self._element_kwargs = kwargs
        self._handlers["websocket:_stream"] = {"uri": "/stream"}

    async def _stream(
        self, request: request.Request, socket: WebSocketCommonProtocol
    ) -> None:
        layout = Layout(
            self._element_constructor(*self._element_args, **self._element_kwargs)
        )

        async def sock_recv() -> Any:
            message = json.loads(await socket.recv())
            return message["body"]["event"]

        async def sock_send(data: Dict[str, Any]) -> None:
            message = {"header": {}, "body": {"render": data}}
            await socket.send(json.dumps(message))

        await SingleStateRenderer(layout).run(sock_send, sock_recv, None)


class SharedServer(SimpleServer):
    def __init__(
        self, element_constructor: ElementConstructor, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(element_constructor, *args, **kwargs)
        self._handlers["listener:_setup_renderer"] = {"event": "before_server_start"}

    async def _setup_renderer(
        self, app: Sanic, loop: asyncio.AbstractEventLoop
    ) -> None:
        root = self._element_constructor(*self._element_args, **self._element_kwargs)
        self._renderer = SharedStateRenderer(Layout(root, loop=loop))

    async def _stream(
        self, request: request.Request, socket: WebSocketCommonProtocol
    ) -> None:
        async def sock_recv() -> Any:
            message = json.loads(await socket.recv())
            return message["body"]["event"]

        async def sock_send(data: Dict[str, Any]) -> None:
            message = {"header": {}, "body": {"render": data}}
            await socket.send(json.dumps(message))

        await self._renderer.run(sock_send, sock_recv, uuid.uuid4().hex)
