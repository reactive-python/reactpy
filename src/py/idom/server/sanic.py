import asyncio
import json
from pathlib import Path
import uuid

from typing import Tuple, Any, Dict, Union

from sanic import Sanic, request, response
from sanic_cors import CORS
from mypy_extensions import TypedDict
from websockets import WebSocketCommonProtocol

from idom.core.render import (
    SingleStateRenderer,
    SharedStateRenderer,
    SendCoroutine,
    RecvCoroutine,
)
from idom.core.layout import LayoutEvent
from idom.core.utils import STATIC_DIRECTORY

from .base import AbstractRenderServer


class Config(TypedDict, total=False):
    cors: Union[bool, Dict[str, Any]]
    url_prefix: str
    webpage_route: bool


class SanicRenderServer(AbstractRenderServer[Sanic, Config]):
    """Base ``sanic`` extension."""

    async def _run_renderer(self, send: SendCoroutine, recv: RecvCoroutine) -> None:
        raise NotImplementedError()

    def _init_config(self) -> Config:
        return Config(cors=False, url_prefix="", webpage_route=True)

    def _update_config(self, old: Config, new: Config) -> Config:
        old.update(new)
        return old

    def _default_application(self, config: Config) -> Sanic:
        return Sanic()

    def _setup_application(self, app: Sanic, config: Config) -> None:
        cors_config = config["cors"]
        if isinstance(cors_config, dict):
            CORS(app, **cors_config)
        elif cors_config:
            CORS(app)
        url_prefix = config["url_prefix"]
        if config["webpage_route"]:
            app.route(url_prefix + "/client/<path:path>")(self._client_route)
        app.websocket(url_prefix + "/stream")(self._stream_route)

    def _run_application(
        self, app: Sanic, config: Config, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> None:
        if not self._daemonized:
            app.run(*args, **kwargs)
        else:
            # copied from:
            # https://github.com/huge-success/sanic/blob/master/examples/run_async_advanced.py
            asyncio.set_event_loop(asyncio.new_event_loop())
            serv_coro = app.create_server(*args, **kwargs, return_asyncio_server=True)
            loop = asyncio.get_event_loop()
            serv_task = asyncio.ensure_future(serv_coro, loop=loop)
            server = loop.run_until_complete(serv_task)
            server.after_start()
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                loop.stop()
            finally:
                server.before_stop()

                # Wait for server to close
                close_task = server.close()
                loop.run_until_complete(close_task)

                # Complete all tasks on the loop
                for connection in server.connections:
                    connection.close_if_idle()
                server.after_stop()

    async def _stream_route(
        self, request: request.Request, socket: WebSocketCommonProtocol
    ) -> None:
        async def sock_recv() -> LayoutEvent:
            message = json.loads(await socket.recv())
            event = message["body"]["event"]
            return LayoutEvent(event["target"], event["data"])

        async def sock_send(data: Dict[str, Any]) -> None:
            message = {"header": {}, "body": {"render": data}}
            await socket.send(json.dumps(message, separators=(",", ":")))

        await self._run_renderer(sock_send, sock_recv)

    async def _client_route(
        self, request: request.Request, path: str
    ) -> response.HTTPResponse:
        client_path = Path(STATIC_DIRECTORY).joinpath("simple-client", *path.split("/"))
        if client_path.exists():
            return await response.file_stream(str(client_path))
        return response.text(f"Could not find: {path!r}", status=404)


class PerClientState(SanicRenderServer):
    """Each client view will have its own state."""

    _renderer_type = SingleStateRenderer

    async def _run_renderer(self, send: SendCoroutine, recv: RecvCoroutine) -> None:
        await self._make_renderer().run(send, recv, None)


class SharedClientState(SanicRenderServer):
    """All connected client views will have shared state."""

    _renderer_type = SharedStateRenderer

    def _setup_application(self, app: Sanic, config: Config) -> None:
        super()._setup_application(app, config)
        app.listener("before_server_start")(self._setup_renderer)

    async def _setup_renderer(
        self, app: Sanic, loop: asyncio.AbstractEventLoop
    ) -> None:
        self._renderer = self._make_renderer(loop)

    async def _run_renderer(self, send: SendCoroutine, recv: RecvCoroutine) -> None:
        await self._renderer.run(send, recv, uuid.uuid4().hex)
