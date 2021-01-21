import json
import asyncio
from threading import Event as ThreadEvent
from urllib.parse import urljoin
from asyncio import Queue as AsyncQueue
from typing import Optional, Type, Any, List, Tuple, Dict

from tornado.web import Application, StaticFileHandler, RedirectHandler
from tornado.websocket import WebSocketHandler
from tornado.platform.asyncio import AsyncIOMainLoop
from typing_extensions import TypedDict

from idom.core.layout import Layout, LayoutUpdate, LayoutEvent
from idom.core.component import ComponentConstructor
from idom.core.dispatcher import AbstractDispatcher, SingleViewDispatcher
from idom.client.manage import BUILD_DIR

from .base import AbstractRenderServer


class Config(TypedDict):
    """Render server config for :class:`TornadoRenderServer` subclasses"""

    base_url: str
    serve_static_files: bool
    redirect_root_to_index: bool


class TornadoRenderServer(AbstractRenderServer[Application, Config]):
    """A base class for all Tornado render servers"""

    _model_stream_handler_type: Type[WebSocketHandler]

    def stop(self):
        try:
            loop = self._loop
        except AttributeError:  # pragma: no cover
            raise RuntimeError(
                f"Application is not running or was not started by {self}"
            )
        else:
            loop.call_soon_threadsafe(self._loop.stop)

    def _create_config(self, config: Optional[Config]) -> Config:
        return Config(
            {
                "base_url": "",
                "serve_static_files": True,
                "redirect_root_to_index": True,
                **(config or {}),
            }
        )

    def _default_application(self, config: Config) -> Application:
        return Application()

    def _setup_application(
        self,
        config: Config,
        app: Application,
    ) -> None:
        base_url = config["base_url"]
        app.add_handlers(
            r".*",
            [
                (urljoin(base_url, route_pattern),) + tuple(handler_info)
                for route_pattern, *handler_info in self._create_route_handlers(config)
            ],
        )

    def _setup_application_did_start_event(
        self, config: Config, app: Application, event: ThreadEvent
    ) -> None:
        pass

    def _create_route_handlers(self, config: Config) -> List[Tuple[Any, ...]]:
        handlers = [
            (
                "/stream",
                self._model_stream_handler_type,
                {"component_constructor": self._root_component_constructor},
            )
        ]

        if config["serve_static_files"]:
            handlers.append(
                (r"/client/(.*)", StaticFileHandler, {"path": str(BUILD_DIR)})
            )
            if config["redirect_root_to_index"]:
                handlers.append(("/", RedirectHandler, {"url": "./client/index.html"}))

        return handlers

    def _run_application(
        self,
        config: Config,
        app: Application,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._loop = asyncio.get_event_loop()
        AsyncIOMainLoop().install()
        app.listen(port, host, *args, **kwargs)
        self._server_did_start.set()
        asyncio.get_event_loop().run_forever()

    def _run_application_in_thread(
        self,
        config: Config,
        app: Application,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        asyncio.set_event_loop(asyncio.new_event_loop())
        self._run_application(config, app, host, port, args, kwargs)


class PerClientStateModelStreamHandler(WebSocketHandler):
    """A web-socket handler that serves up a new model stream to each new client"""

    _dispatcher_type: Type[AbstractDispatcher] = SingleViewDispatcher
    _dispatcher_inst: AbstractDispatcher
    _message_queue: AsyncQueue

    def initialize(self, component_constructor: ComponentConstructor) -> None:
        self._component_constructor = component_constructor

    async def open(self):
        message_queue = AsyncQueue()
        query_params = {k: v[0].decode() for k, v in self.request.arguments.items()}
        dispatcher = self._dispatcher_type(
            Layout(self._component_constructor(**query_params))
        )

        async def send(value: LayoutUpdate) -> None:
            await self.write_message(json.dumps(value))

        async def recv() -> LayoutEvent:
            return LayoutEvent(**json.loads(await message_queue.get()))

        async def run() -> None:
            await dispatcher.__aenter__()
            await dispatcher.run(send, recv, None)

        asyncio.ensure_future(run())

        self._dispatcher_inst = dispatcher
        self._message_queue = message_queue

    async def on_message(self, message: str) -> None:
        await self._message_queue.put(message)

    def on_close(self):
        asyncio.ensure_future(self._dispatcher_inst.__aexit__(None, None, None))


class PerClientStateServer(TornadoRenderServer):
    """Each client view will have its own state."""

    _model_stream_handler_type = PerClientStateModelStreamHandler
