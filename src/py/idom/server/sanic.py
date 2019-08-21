import asyncio
import json
import os
from sanic import Sanic, request, response
import uuid
from websockets import WebSocketCommonProtocol

from typing import Tuple, Any, Dict

from idom.core.render import (
    SingleStateRenderer,
    SharedStateRenderer,
    SendCoroutine,
    RecvCoroutine,
)
from idom.core.layout import Layout
from idom.core.utils import STATIC_DIRECTORY

from .base import AbstractServerExtension, Config


class SanicServerExtension(AbstractServerExtension):
    """Base ``sanic`` extension."""

    def _init_config(self, config: Config) -> None:
        config.update(url_prefix="", webpage_route=True)

    def _default_application(self, config: Config) -> Sanic:
        return Sanic()

    def _setup_application(self, app: Sanic, config: Config) -> None:
        if config["webpage_route"]:
            app.route(config["url_prefix"] + "/client/<path:path>")(self._webpage)
        app.websocket(config["url_prefix"] + "/stream")(self._stream)

    def _run_application(
        self, app: Sanic, config: Config, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> None:
        if self._daemonized:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            server = app.create_server(*args, **kwargs)
            asyncio.ensure_future(server)
            loop.run_forever()
        else:
            app.run(*args, **kwargs)

    async def _stream(
        self, request: request.Request, socket: WebSocketCommonProtocol
    ) -> None:
        async def sock_recv() -> Any:
            message = json.loads(await socket.recv())
            return message["body"]["event"]

        async def sock_send(data: Dict[str, Any]) -> None:
            message = {"header": {}, "body": {"render": data}}
            await socket.send(json.dumps(message, separators=(",", ":")))

        await self._run_renderer(sock_send, sock_recv)

    async def _run_renderer(self, send: SendCoroutine, recv: RecvCoroutine) -> None:
        raise NotImplementedError()

    async def _webpage(
        self, request: request.Request, path: str
    ) -> response.HTTPResponse:
        return await response.file(
            os.path.join(STATIC_DIRECTORY, "simple-client", *path.split("/"))
        )


class PerClientState(SanicServerExtension):
    """Each client view will have its own state."""

    async def _run_renderer(self, send: SendCoroutine, recv: RecvCoroutine) -> None:
        element = self._element_constructor(*self._element_args, **self._element_kwargs)
        await SingleStateRenderer(Layout(element)).run(send, recv, None)


class SharedClientState(SanicServerExtension):
    """All connected client views will have shared state."""

    def _setup_application(self, app: Sanic, config: Config) -> None:
        super()._setup_application(app, config)
        app.listener("before_server_start")(self._setup_renderer)

    async def _setup_renderer(
        self, app: Sanic, loop: asyncio.AbstractEventLoop
    ) -> None:
        self._renderer = SharedStateRenderer(Layout(self._create_element(), loop=loop))

    async def _run_renderer(self, send: SendCoroutine, recv: RecvCoroutine) -> None:
        await self._renderer.run(send, recv, uuid.uuid4().hex)
