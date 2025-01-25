import asyncio
import logging
import re
import urllib.parse
from collections.abc import Coroutine, Iterable
from concurrent.futures import Future
from importlib import import_module
from pathlib import Path
from threading import Thread
from typing import Any, Callable

import orjson
from asgiref.compatibility import guarantee_single_callable
from servestatic import ServeStaticASGI

from reactpy.backend.types import Connection, Location
from reactpy.backend.utils import check_path, import_components, normalize_url_path
from reactpy.config import REACTPY_WEB_MODULES_DIR
from reactpy.core.hooks import ConnectionContext
from reactpy.core.layout import Layout
from reactpy.core.serve import serve_layout
from reactpy.core.types import ComponentType

_logger = logging.getLogger(__name__)
_backhaul_loop = asyncio.new_event_loop()


def start_backhaul_loop():
    """Starts the asyncio event loop that will perform component rendering
    tasks."""
    asyncio.set_event_loop(_backhaul_loop)
    _backhaul_loop.run_forever()


_backhaul_thread = Thread(target=start_backhaul_loop, daemon=True)


class ReactPyMiddleware:
    def __init__(
        self,
        app: Callable[..., Coroutine],
        root_components: Iterable[str],
        *,
        # TODO: Add a setting attribute to this class. Or maybe just put a shit ton of kwargs here. Or add a **kwargs that resolves to a TypedDict?
        path_prefix: str = "reactpy/",
        web_modules_dir: Path | None = None,
    ) -> None:
        """Configure the ASGI app. Anything initialized in this method will be shared across all future requests."""
        # Configure class attributes
        self.path_prefix = normalize_url_path(path_prefix)
        self.dispatcher_path = f"/{self.path_prefix}/"
        self.web_modules_path = f"/{self.path_prefix}/modules/"
        self.static_path = f"/{self.path_prefix}/static/"
        self.dispatcher_pattern = re.compile(
            f"^{self.dispatcher_path}(?P<dotted_path>[^/]+)/?"
        )
        self.js_modules_pattern = re.compile(f"^{self.web_modules_path}.*")
        self.static_pattern = re.compile(f"^{self.static_path}.*")
        self.web_modules_dir = web_modules_dir or REACTPY_WEB_MODULES_DIR.current
        self.static_dir = Path(__file__).parent.parent / "static"
        self.backhaul_thread = False  # TODO: Add backhaul_thread settings
        self.user_app = guarantee_single_callable(app)
        self.servestatic_static: ServeStaticASGI | None = None
        self.servestatic_web_modules: ServeStaticASGI | None = None
        self.component_dotted_paths = set(root_components)
        self.components: dict[str, ComponentType] = import_components(
            self.component_dotted_paths
        )
        self.dispatcher: Future | asyncio.Task | None = None
        self.recv_queue: asyncio.Queue = asyncio.Queue()
        if self.web_modules_dir != REACTPY_WEB_MODULES_DIR.current:
            REACTPY_WEB_MODULES_DIR.set_current(self.web_modules_dir)

        # Start the backhaul thread if it's not already running
        if self.backhaul_thread and not _backhaul_thread.is_alive():
            _backhaul_thread.start()

        # Validate the arguments
        reason = check_path(self.path_prefix)
        if reason:
            raise ValueError(f"Invalid `path_prefix`. {reason}")

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """The ASGI entrypoint that determines whether ReactPy should route the
        request to ourselves or to the user application."""
        # URL routing for the ReactPy renderer
        if scope["type"] == "websocket" and self.match_dispatch_path(scope):
            return await self.component_dispatch_app(scope, receive, send)

        # URL routing for ReactPy web modules
        if scope["type"] == "http" and re.match(self.js_modules_pattern, scope["path"]):
            return await self.web_module_app(scope, receive, send)

        # URL routing for ReactPy static files
        if scope["type"] == "http" and re.match(self.static_pattern, scope["path"]):
            return await self.static_file_app(scope, receive, send)

        # Serve the user's application
        await self.user_app(scope, receive, send)

    async def component_dispatch_app(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """ASGI app for rendering ReactPy Python components."""
        ws_connected: bool = False

        while True:
            # Future WS events on this connection will always be received here
            event = await receive()

            if event["type"] == "websocket.connect" and not ws_connected:
                ws_connected = True
                await send({"type": "websocket.accept"})
                run_dispatcher_coro = self.run_dispatcher(scope, receive, send)
                if self.backhaul_thread:
                    self.dispatcher = asyncio.run_coroutine_threadsafe(
                        run_dispatcher_coro, _backhaul_loop
                    )
                else:
                    self.dispatcher = asyncio.create_task(run_dispatcher_coro)

            if event["type"] == "websocket.disconnect":
                if self.dispatcher:
                    self.dispatcher.cancel()
                break

            if event["type"] == "websocket.receive":
                queue_put_coro = self.recv_queue.put(orjson.loads(event["text"]))
                if self.backhaul_thread:
                    asyncio.run_coroutine_threadsafe(queue_put_coro, _backhaul_loop)
                else:
                    await queue_put_coro

    async def web_module_app(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """ASGI app for ReactPy web modules."""
        if not self.web_modules_dir:
            await asyncio.to_thread(
                _logger.info,
                "Tried to serve web module without a configured directory.",
            )
            return await self.user_app(scope, receive, send)

        if not self.servestatic_web_modules:
            self.servestatic_web_modules = ServeStaticASGI(
                self.user_app,
                root=self.web_modules_dir,
                prefix=self.web_modules_path,
                autorefresh=True,
            )

        return await self.servestatic_web_modules(scope, receive, send)

    async def static_file_app(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """ASGI app for ReactPy static files."""
        # If no static directory is configured, serve the user's application
        if not self.static_dir:
            await asyncio.to_thread(
                _logger.info,
                "Tried to serve static file without a configured directory.",
            )
            return await self.user_app(scope, receive, send)

        if not self.servestatic_static:
            self.servestatic_static = ServeStaticASGI(
                self.user_app, root=self.static_dir, prefix=self.static_path
            )

        return await self.servestatic_static(scope, receive, send)

    async def run_dispatcher(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        # Get the component from the URL.
        url_path = re.match(self.dispatcher_pattern, scope["path"])
        if not url_path:
            raise RuntimeError("Could not find component in URL path.")
        dotted_path = url_path[1]
        module_str, component_str = dotted_path.rsplit(".", 1)
        module = import_module(module_str)
        component = getattr(module, component_str)
        parsed_url = urllib.parse.urlparse(scope["path"])

        await serve_layout(
            Layout(  # type: ignore
                ConnectionContext(
                    component(),
                    value=Connection(
                        scope=scope,
                        location=Location(
                            parsed_url.path,
                            f"?{parsed_url.query}" if parsed_url.query else "",
                        ),
                        carrier={
                            "scope": scope,
                            "send": send,
                            "receive": receive,
                        },
                    ),
                )
            ),
            self.send_json_ws(send),
            self.recv_queue.get,
        )

    @staticmethod
    def send_json_ws(send: Callable) -> Callable[..., Coroutine]:
        """Use orjson to send JSON over an ASGI websocket."""

        async def _send_json(value: Any) -> None:
            await send({"type": "websocket.send", "text": orjson.dumps(value)})

        return _send_json

    def match_dispatch_path(self, scope: dict) -> bool:
        match = re.match(self.dispatcher_pattern, scope["path"])
        return bool(
            match
            and match.groupdict().get("dotted_path") in self.component_dotted_paths
        )
