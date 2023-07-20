import asyncio
import logging
import mimetypes
import os
import re
import urllib.parse
from collections.abc import Coroutine, Sequence
from pathlib import Path
from threading import Thread

import aiofiles
import orjson
from asgiref.compatibility import guarantee_single_callable

from reactpy.backend._common import (
    CLIENT_BUILD_DIR,
    safe_join_path,
    vdom_head_elements_to_html,
)
from reactpy.backend.hooks import ConnectionContext
from reactpy.backend.mimetypes import MIME_TYPES
from reactpy.backend.types import Connection, Location
from reactpy.config import REACTPY_WEB_MODULES_DIR
from reactpy.core.layout import Layout
from reactpy.core.serve import serve_layout
from reactpy.core.types import ComponentConstructor, VdomDict

_logger = logging.getLogger(__name__)
_backhaul_loop = asyncio.new_event_loop()


def start_backhaul_loop():
    """Starts the asyncio event loop that will perform component rendering tasks."""
    asyncio.set_event_loop(_backhaul_loop)
    _backhaul_loop.run_forever()


_backhaul_thread = Thread(target=start_backhaul_loop, daemon=True)


class ReactPy:
    def __init__(
        self,
        app_or_component: ComponentConstructor | Coroutine,
        *,
        dispatcher_path: str = "^reactpy/([^/]+)/?",
        js_modules_path: str | None = "^reactpy/modules/([^/]+)/?",
        static_path: str | None = "^reactpy/static/([^/]+)/?",
        static_dir: Path | str | None = None,
        head: Sequence[VdomDict] | VdomDict | str = "",
        backhaul_thread: bool = True,
        block_size: int = 8192,
    ) -> None:
        self.component = (
            app_or_component
            if isinstance(app_or_component, ComponentConstructor)
            else None
        )
        self.user_app = (
            guarantee_single_callable(app_or_component)
            if not self.component and asyncio.iscoroutinefunction(app_or_component)
            else None
        )
        if not self.component and not self.user_app:
            raise TypeError(
                "The first argument to ReactPy(...) must be a component or an ASGI application."
            )
        self.dispatch_path = re.compile(dispatcher_path)
        self.js_modules_path = re.compile(js_modules_path) if js_modules_path else None
        self.static_path = re.compile(static_path) if static_path else None
        self.static_dir = static_dir
        self.all_paths = re.compile(
            "|".join(
                path for path in [dispatcher_path, js_modules_path, static_path] if path
            )
        )
        self.head = vdom_head_elements_to_html(head)
        self._cached_index_html = ""
        self.connected = False
        self.backhaul_thread = backhaul_thread
        self.dispatcher = None
        self.block_size = block_size
        if self.backhaul_thread and not _backhaul_thread.is_alive():
            _backhaul_thread.start()

    async def __call__(self, scope, receive, send) -> None:
        """The ASGI callable. This determines whether ReactPy should route the the
        request to ourselves or to the user application."""
        # Determine if ReactPy should handle the request
        if not self.user_app or re.match(self.all_paths, scope["path"]):
            await self.reactpy_app(scope, receive, send)
            return

        # Serve the user's application
        await self.user_app(scope, receive, send)

    async def reactpy_app(self, scope, receive, send) -> None:
        """Determine what type of request this is and route it to the appropriate
        ReactPy ASGI sub-application."""

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
        if self.js_modules_path and re.match(self.js_modules_path, scope["path"]):
            await self.js_modules_app(scope, receive, send)
            return

        # Static file app
        if self.static_path and re.match(self.static_path, scope["path"]):
            await self.static_file_app(scope, receive, send)
            return

        # Standalone app: Serve a single component using index.html
        if self.component:
            await self.standalone_app(scope, receive, send)
            return

    async def component_dispatch_app(self, scope, receive, send) -> None:
        """ASGI app for rendering ReactPy Python components."""
        while True:
            event = await receive()

            if event["type"] == "websocket.connect" and not self.connected:
                self.connected = True
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

    async def js_modules_app(self, scope, receive, send) -> None:
        """ASGI app for ReactPy web modules."""
        if not REACTPY_WEB_MODULES_DIR.current:
            raise RuntimeError("No web modules directory configured.")

        # Make sure the user hasn't tried to escape the web modules directory
        try:
            abs_file_path = safe_join_path(
                REACTPY_WEB_MODULES_DIR.current,
                re.match(self.js_modules_path, scope["path"])[1],
            )
        except ValueError:
            await http_response(scope, send, 403, "Forbidden")
            return

        # Serve the file
        await file_response(scope, send, abs_file_path, self.block_size)

    async def static_file_app(self, scope, receive, send) -> None:
        """ASGI app for ReactPy static files."""
        if not self.static_dir:
            raise RuntimeError(
                "Static files cannot be served without defining `static_dir`."
            )

        # Make sure the user hasn't tried to escape the static directory
        try:
            abs_file_path = safe_join_path(
                self.static_dir,
                re.match(self.static_path, scope["path"])[1],
            )
        except ValueError:
            await http_response(scope, send, 403, "Forbidden")
            return

        # Serve the file
        await file_response(scope, send, abs_file_path, self.block_size)

    async def standalone_app(self, scope, receive, send) -> None:
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

    async def run_dispatcher(self, scope, receive, send):
        # If in standalone mode, serve the user provided component.
        # In middleware mode, get the component from the URL.
        component = self.component or re.match(self.dispatch_path, scope["path"])[1]
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


def send_json(send) -> None:
    """Use orjson to send JSON over an ASGI websocket."""

    async def _send_json(value) -> None:
        await send({"type": "websocket.send", "text": orjson.dumps(value)})

    return _send_json


async def http_response(
    scope,
    send,
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


async def file_response(scope, send, file_path: Path, block_size: int) -> None:
    """Send a file in chunks."""
    # Make sure the file exists
    if not await asyncio.to_thread(os.path.exists, file_path):
        await http_response(scope, send, 404, "File not found.")
        return

    # Make sure it's a file
    if not await asyncio.to_thread(os.path.isfile, file_path):
        await http_response(scope, send, 400, "Not a file.")
        return

    # Check if the file is already cached by the client
    etag = await header_val(scope, b"etag")
    modification_time = await asyncio.to_thread(os.path.getmtime, file_path)
    if etag and etag != modification_time:
        await http_response(scope, send, 304, "Not modified.")
        return

    # Get the file's MIME type
    mime_type = (
        MIME_TYPES.get(file_path.rsplit(".")[1], None)
        # Fallback to guess_type to allow for the user to define custom MIME types on their system
        or (await asyncio.to_thread(mimetypes.guess_type, file_path, strict=False))[0]
    )
    if mime_type is None:
        mime_type = "text/plain"
        _logger.error(
            f"Could not determine MIME type for {file_path}. Defaulting to 'text/plain'."
        )

    # Send the file in chunks
    file_size = await asyncio.to_thread(os.path.getsize, file_path)
    async with aiofiles.open(file_path, "rb") as file_handle:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", mime_type.encode()),
                    (b"etag", modification_time),
                    (b"content-length", file_size),
                ],
            }
        )

        # Head requests don't need a body
        if scope["method"] != "HEAD":
            while True:
                chunk = await file_handle.read(block_size)
                more_body = bool(chunk)
                await send(
                    {
                        "type": "http.response.body",
                        "body": chunk,
                        "more_body": more_body,
                    }
                )
                if not more_body:
                    break


async def header_val(scope: dict, key: str, default: str | int | None = None) -> str | int | None:
    """Get a value from a scope's headers."""
    return await anext(
        (
            value.decode()
            for header_key, value in scope["headers"]
            if header_key == key.encode()
        ),
        default,
    )
