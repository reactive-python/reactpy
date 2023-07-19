import asyncio
import logging
import mimetypes
import os
import re
import urllib.parse
from collections.abc import Coroutine, Sequence
from pathlib import Path

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

DEFAULT_BLOCK_SIZE = 8192
_logger = logging.getLogger(__name__)


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
                "The first argument to `ReactPy` must be a component or an ASGI application."
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

    async def __call__(self, scope, receive, send) -> None:
        """The ASGI callable. This determines whether ReactPy should route the the
        request to ourselves or to the user application."""

        # Determine if ReactPy should handle the request
        if not self.user_app or re.match(self.all_paths, scope["path"]):
            # Dispatch a Python component
            if scope["type"] == "websocket" and re.match(
                self.dispatch_path, scope["path"]
            ):
                await self.component_dispatch_app(scope, receive, send)
                return

            # User tried to use an unsupported HTTP method
            if scope["type"] == "http" and scope["method"] not in ("GET", "HEAD"):
                await simple_response(
                    scope, send, status=405, content="Method Not Allowed"
                )
                return

            # Route requests to our JS web module app
            if (
                scope["type"] == "http"
                and self.js_modules_path
                and re.match(self.js_modules_path, scope["path"])
            ):
                await self.js_modules_app(scope, receive, send)
                return

            # Route requests to our static file server app
            if (
                scope["type"] == "http"
                and self.static_path
                and re.match(self.static_path, scope["path"])
            ):
                await self.static_file_app(scope, receive, send)
                return

            # Route all other requests to serve a component (user is in standalone mode)
            if scope["type"] == "http" and self.component:
                await self.index_html_app(scope, receive, send)
                return

        # Serve the user's application
        if self.user_app:
            await self.user_app(scope, receive, send)
            return

        _logger.error("ReactPy appears to be misconfigured. Request not handled.")

    async def component_dispatch_app(self, scope, receive, send) -> None:
        """The ASGI application for ReactPy Python components."""

        self._reactpy_recv_queue: asyncio.Queue = asyncio.Queue()
        parsed_url = urllib.parse.urlparse(scope["path"])

        # If in standalone mode, serve the user provided component.
        # In middleware mode, get the component from the URL.
        component = self.component or re.match(self.dispatch_path, scope["path"])[1]

        while True:
            event = await receive()

            if event["type"] == "websocket.connect":
                await send({"type": "websocket.accept"})

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
                    self._reactpy_recv_queue.get,
                )

            if event["type"] == "websocket.disconnect":
                break

            if event["type"] == "websocket.receive":
                await self._reactpy_recv_queue.put(orjson.loads(event["text"]))

    async def js_modules_app(self, scope, receive, send) -> None:
        """The ASGI application for ReactPy web modules."""

        if not REACTPY_WEB_MODULES_DIR.current:
            raise RuntimeError("No web modules directory configured.")

        # Make sure the user hasn't tried to escape the web modules directory
        try:
            abs_file_path = safe_join_path(
                REACTPY_WEB_MODULES_DIR.current,
                REACTPY_WEB_MODULES_DIR.current,
                re.match(self.js_modules_path, scope["path"])[1],
            )
        except ValueError:
            await simple_response(send, 403, "Forbidden")
            return

        # Serve the file
        await file_response(scope, send, abs_file_path)

    async def static_file_app(self, scope, receive, send) -> None:
        """The ASGI application for ReactPy static files."""

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
            await simple_response(send, 403, "Forbidden")
            return

        # Serve the file
        await file_response(scope, send, abs_file_path)

    async def index_html_app(self, scope, receive, send) -> None:
        """The ASGI application for ReactPy index.html."""

        # TODO: We want to respect the if-modified-since header, but currently can't
        # due to the fact that our HTML is not statically rendered.
        file_path = CLIENT_BUILD_DIR / "index.html"
        if not self._cached_index_html:
            async with aiofiles.open(file_path, "rb") as file_handle:
                self._cached_index_html = str(await file_handle.read()).format(
                    __head__=self.head
                )

        # Head requests don't need a body
        if scope["method"] == "HEAD":
            await simple_response(
                send,
                200,
                "",
                content_type=b"text/html",
                headers=[(b"cache-control", b"no-cache")],
            )
            return

        # Send the index.html
        await simple_response(
            send,
            200,
            self._cached_index_html,
            content_type=b"text/html",
            headers=[(b"cache-control", b"no-cache")],
        )


def send_json(send) -> None:
    """Use orjson to send JSON over an ASGI websocket."""

    async def _send_json(value) -> None:
        await send({"type": "websocket.send", "text": orjson.dumps(value)})

    return _send_json


async def simple_response(
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
            "headers": [(b"content-type", content_type, *headers)],
        }
    )
    await send({"type": "http.response.body", "body": message.encode()})


async def file_response(scope, send, file_path: Path) -> None:
    """Send a file in chunks."""

    # Make sure the file exists
    if not await asyncio.to_thread(os.path.exists, file_path):
        await simple_response(send, 404, "File not found.")
        return

    # Make sure it's a file
    if not await asyncio.to_thread(os.path.isfile, file_path):
        await simple_response(send, 400, "Not a file.")
        return

    # Check if the file is already cached by the client
    etag = await get_val_from_header(scope, b"ETag")
    if etag and etag != await asyncio.to_thread(
        os.path.getmtime, file_path
    ):
        await simple_response(send, 304, "Not modified.")
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
    async with aiofiles.open(file_path, "rb") as file_handle:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", mime_type.encode()),
                    (
                        b"ETag",
                        str(
                            await asyncio.to_thread(os.path.getmtime, file_path)
                        ).encode(),
                    ),
                ],
            }
        )

        # Head requests don't need a body
        if scope["method"] == "HEAD":
            return

        while True:
            chunk = await file_handle.read(DEFAULT_BLOCK_SIZE)
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


async def get_val_from_header(
    scope: dict, key: str, default: str | None = None
) -> str | None:
    """Get a value from a scope's headers."""

    return await anext(
        (
            value.decode()
            for header_key, value in scope["headers"]
            if header_key == key.encode()
        ),
        default,
    )
