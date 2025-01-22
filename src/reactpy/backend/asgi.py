import asyncio
import logging
import re
import urllib.parse
from collections.abc import Coroutine, Sequence
from concurrent.futures import Future
from importlib import import_module
from pathlib import Path
from threading import Thread
from typing import Any, Callable

import aiofiles
import orjson
from asgiref.compatibility import guarantee_single_callable
from starlette.staticfiles import StaticFiles

from reactpy.backend._common import (
    CLIENT_BUILD_DIR,
    vdom_head_elements_to_html,
)
from reactpy.backend.hooks import ConnectionContext
from reactpy.backend.types import Connection, Location
from reactpy.config import REACTPY_WEB_MODULES_DIR
from reactpy.core.component import Component
from reactpy.core.layout import Layout
from reactpy.core.serve import serve_layout
from reactpy.core.types import ComponentType, VdomDict

_logger = logging.getLogger(__name__)
_backhaul_loop = asyncio.new_event_loop()


def start_backhaul_loop():
    """Starts the asyncio event loop that will perform component rendering
    tasks."""
    asyncio.set_event_loop(_backhaul_loop)
    _backhaul_loop.run_forever()


_backhaul_thread = Thread(target=start_backhaul_loop, daemon=True)


class ReactPy:
    def __init__(
        self,
        app_or_component: ComponentType | Callable[..., Coroutine],
        *,
        dispatcher_path: str = "reactpy/",
        web_modules_path: str = "reactpy/modules/",
        web_modules_dir: Path | str | None = REACTPY_WEB_MODULES_DIR.current,
        static_path: str = "reactpy/static/",
        static_dir: Path | str | None = None,
        head: Sequence[VdomDict] | VdomDict | str = "",
        backhaul_thread: bool = True,
        block_size: int = 8192,
    ) -> None:
        """Anything initialized in this method will be shared across all
        requests."""
        # Convert kwargs to class attributes
        self.dispatch_path = re.compile(f"^{dispatcher_path}(?P<dotted_path>[^/]+)/?")
        self.js_modules_path = re.compile(f"^{web_modules_path}")
        self.web_modules_dir = web_modules_dir
        self.static_path = re.compile(f"^{static_path}")
        self.static_dir = static_dir
        self.head = vdom_head_elements_to_html(head)
        self.backhaul_thread = backhaul_thread
        self.block_size = block_size

        # Internal attributes (not using the same name as a kwarg)
        self.user_app: Callable[..., Coroutine] | None = (
            guarantee_single_callable(app_or_component)
            if asyncio.iscoroutinefunction(app_or_component)
            else None
        )
        self.component: ComponentType | None = (
            None if self.user_app else app_or_component  # type: ignore
        )
        self.all_paths: re.Pattern = re.compile(
            "|".join(
                path
                for path in [dispatcher_path, web_modules_path, static_path]
                if path
            )
        )
        self.dispatcher: Future | asyncio.Task | None = None
        self._cached_index_html: str = ""
        self._static_file_server: StaticFiles | None = None
        self._web_module_server: StaticFiles | None = None

        # Startup tasks
        if self.backhaul_thread and not _backhaul_thread.is_alive():
            _backhaul_thread.start()
        if self.web_modules_dir != REACTPY_WEB_MODULES_DIR.current:
            REACTPY_WEB_MODULES_DIR.set_current(self.web_modules_dir)

        # Validate the arguments
        if not self.component and not self.user_app:
            raise TypeError(
                "The first argument to ReactPy(...) must be a component or an "
                "ASGI application."
            )
        if not check_path(dispatcher_path):
            raise ValueError("Invalid `dispatcher_path`.")
        if not check_path(web_modules_path):
            raise ValueError("Invalid `web_modules_path`.")
        if not check_path(static_path):
            raise ValueError("Invalid `static_path`.")

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """The ASGI callable. This determines whether ReactPy should route the
        request to ourselves or to the user application."""
        # Determine if ReactPy should handle the request
        if not self.user_app or re.match(self.all_paths, scope["path"]):
            await self.reactpy_app(scope, receive, send)
            return

        # Serve the user's application
        await self.user_app(scope, receive, send)

    async def reactpy_app(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """Determine what type of request this is and route it to the
        appropriate ReactPy ASGI sub-application."""
        # Only HTTP and WebSocket requests are supported
        if scope["type"] not in {"http", "websocket"}:
            return

        # Dispatch a Python component
        if scope["type"] == "websocket" and re.match(self.dispatch_path, scope["path"]):
            await self.component_dispatch_app(scope, receive, send)
            return

        # Only HTTP GET and HEAD requests are supported
        if scope["method"] not in {"GET", "HEAD"}:
            await http_response(scope, send, 405, "Method Not Allowed")
            return

        # JS modules app
        if re.match(self.js_modules_path, scope["path"]):
            await self.web_module_app(scope, receive, send)
            return

        # Static file app
        if re.match(self.static_path, scope["path"]):
            await self.static_file_app(scope, receive, send)
            return

        # Standalone app: Serve a single component using index.html
        if self.component:
            await self.standalone_app(scope, receive, send)
            return

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
                run_dispatcher = self.run_dispatcher(scope, receive, send)
                if self.backhaul_thread:
                    self.dispatcher = asyncio.run_coroutine_threadsafe(
                        run_dispatcher, _backhaul_loop
                    )
                else:
                    self.dispatcher = asyncio.create_task(run_dispatcher)

            if event["type"] == "websocket.disconnect":
                if self.dispatcher:
                    self.dispatcher.cancel()
                break

            if event["type"] == "websocket.receive":
                recv_queue_put = self.recv_queue.put(orjson.loads(event["text"]))
                if self.backhaul_thread:
                    asyncio.run_coroutine_threadsafe(recv_queue_put, _backhaul_loop)
                else:
                    await recv_queue_put

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
            if self.user_app:
                await self.user_app(scope, receive, send)
            return

        if not self._web_module_server:
            self._web_module_server = StaticFiles(directory=self.web_modules_dir)
        await self._web_module_server(scope, receive, send)

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
            if self.user_app:
                await self.user_app(scope, receive, send)
            return

        if not self._static_file_server:
            self._static_file_server = StaticFiles(directory=self.static_dir)
        await self._static_file_server(scope, receive, send)

    async def standalone_app(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """ASGI app for ReactPy standalone mode."""
        file_path = CLIENT_BUILD_DIR / "index.html"
        if not self._cached_index_html:
            async with aiofiles.open(file_path, "rb") as file_handle:
                self._cached_index_html = str(await file_handle.read()).format(
                    __head__=self.head
                )

        # Send the index.html
        await http_response(
            scope,
            send,
            200,
            self._cached_index_html,
            content_type=b"text/html",
            headers=[
                (b"content-length", len(self._cached_index_html)),
                (b"etag", hash(self._cached_index_html)),
            ],
        )

    async def run_dispatcher(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        # If in standalone mode, serve the user provided component.
        # In middleware mode, get the component from the URL.
        component = self.component
        if not component:
            url_path = re.match(self.dispatch_path, scope["path"])
            if not url_path:
                raise RuntimeError("Could not find component in URL path.")
            dotted_path = url_path[1]
            module_str, component_str = dotted_path.rsplit(".", 1)
            module = import_module(module_str)
            component = getattr(module, component_str)
        parsed_url = urllib.parse.urlparse(scope["path"])
        self.recv_queue: asyncio.Queue = asyncio.Queue()

        await serve_layout(
            Layout(
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
            send_json(send),
            self.recv_queue.get,
        )


def send_json(send: Callable) -> Callable[..., Coroutine]:
    """Use orjson to send JSON over an ASGI websocket."""

    async def _send_json(value: Any) -> None:
        await send({"type": "websocket.send", "text": orjson.dumps(value)})

    return _send_json


async def http_response(
    scope: dict[str, Any],
    send: Callable[..., Coroutine],
    code: int,
    message: str,
    content_type: bytes = b"text/plain",
    headers: Sequence = (),
) -> None:
    """Send a simple response."""
    await send(
        {
            "type": "http.response.start",
            "status": code,
            "headers": [(b"content-type", content_type), *headers],
        }
    )
    # Head requests don't need a body
    if scope["method"] != "HEAD":
        await send({"type": "http.response.body", "body": message.encode()})


def check_path(url_path: str) -> bool:
    """Check that a path is valid URL path."""
    return (
        not url_path
        or not isinstance(url_path, str)
        or not url_path[0].isalnum()
        or not url_path.endswith("/")
    )
