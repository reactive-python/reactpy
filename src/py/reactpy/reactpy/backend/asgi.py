import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Sequence

import aiofiles
from asgiref.compatibility import guarantee_single_callable

from reactpy.backend._common import (
    CLIENT_BUILD_DIR,
    traversal_safe_path,
    vdom_head_elements_to_html,
)
from reactpy.backend.mimetypes import DEFAULT_MIME_TYPES
from reactpy.config import REACTPY_WEB_MODULES_DIR
from reactpy.core.types import VdomDict

DEFAULT_STATIC_PATH = f"{os.getcwd()}/static"
DEFAULT_BLOCK_SIZE = 8192
_logger = logging.getLogger(__name__)


class ReactPy:
    def __init__(
        self,
        application=None,
        dispatcher_path: str = "^reactpy/stream/([^/]+)/?",
        js_modules_path: str | None = "^reactpy/modules/([^/]+)/?",
        static_path: str | None = "^reactpy/static/([^/]+)/?",
        static_dir: str | None = DEFAULT_STATIC_PATH,
        head: Sequence[VdomDict] | VdomDict | str = "",
    ) -> None:
        self.user_app = guarantee_single_callable(application)
        self.dispatch_path = re.compile(dispatcher_path)
        self.js_modules_path = re.compile(js_modules_path)
        self.static_path = re.compile(static_path)
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
            if scope["method"] not in ("GET", "HEAD"):
                await simple_response(
                    scope, send, status=405, content="Method Not Allowed"
                )
                return

            # Serve a JS web module
            if scope["type"] == "http" and re.match(
                self.js_modules_path, scope["path"]
            ):
                await self.js_modules_app(scope, receive, send)
                return

            # Serve a static file
            if scope["type"] == "http" and re.match(self.static_path, scope["path"]):
                await self.static_file_app(scope, receive, send)
                return

            # Serve index.html
            if scope["type"] == "http":
                await self.index_html_app(scope, receive, send)
                return

        # Serve the user's application
        else:
            await self.user_app(scope, receive, send)

    async def component_dispatch_app(self, scope, receive, send) -> None:
        """The ASGI application for ReactPy Python components."""

    async def js_modules_app(self, scope, receive, send) -> None:
        """The ASGI application for ReactPy web modules."""

        if not REACTPY_WEB_MODULES_DIR.current:
            raise RuntimeError("No web modules directory configured")

        # Get the relative file path from the URL
        file_url_path = re.match(self.js_modules_path, scope["path"])[1]

        # Make sure the user hasn't tried to escape the web modules directory
        try:
            file_path = traversal_safe_path(
                REACTPY_WEB_MODULES_DIR.current,
                REACTPY_WEB_MODULES_DIR.current,
                file_url_path,
            )
        except ValueError:
            await simple_response(send, 403, "Forbidden")
            return

        # Serve the file
        await file_response(scope, send, file_path)

    async def static_file_app(self, scope, receive, send) -> None:
        """The ASGI application for ReactPy static files."""

        if self.static_dir is None:
            raise RuntimeError("No static directory configured")

        # Get the relative file path from the URL
        file_url_path = re.match(self.static_path, scope["path"])[1]

        # Make sure the user hasn't tried to escape the static directory
        try:
            file_path = traversal_safe_path(
                self.static_dir, self.static_dir, file_url_path
            )
        except ValueError:
            await simple_response(send, 403, "Forbidden")
            return

        # Serve the file
        await file_response(scope, send, file_path)

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
    if not os.path.exists(file_path):
        await simple_response(send, 404, "File not found.")
        return

    # Make sure it's a file
    if not os.path.isfile(file_path):
        await simple_response(send, 400, "Not a file.")
        return

    # Check if the file is already cached by the client
    modified_since = await get_val_from_header(scope, b"if-modified-since")
    if modified_since and modified_since > os.path.getmtime(file_path):
        await simple_response(send, 304, "Not modified.")
        return

    # Get the file's MIME type
    mime_type = (
        DEFAULT_MIME_TYPES.get(file_path.rsplit(".")[1], None)
        or mimetypes.guess_type(file_path, strict=False)[0]
    )
    if mime_type is None:
        mime_type = "text/plain"
        _logger.error(f"Could not determine MIME type for {file_path}.")

    # Send the file in chunks
    async with aiofiles.open(file_path, "rb") as file_handle:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", mime_type.encode()),
                    (b"last-modified", str(os.path.getmtime(file_path)).encode()),
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
