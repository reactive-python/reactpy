import hashlib
import os
import re
from collections.abc import Coroutine, Sequence
from email.utils import formatdate
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from reactpy.backend.middleware import ReactPyMiddleware
from reactpy.backend.utils import dict_to_byte_list, find_and_replace
from reactpy.core.types import ComponentType

_logger = getLogger(__name__)


class ReactPyStandalone(ReactPyMiddleware):
    cached_index_html: str = ""
    etag: str = ""
    last_modified: str = ""
    templates_dir = Path(__file__).parent.parent / "templates"
    index_html_path = templates_dir / "index.html"
    single_root_component: bool = True

    def __init__(
        self,
        root_component: ComponentType,
        *,
        path_prefix: str = "reactpy/",
        web_modules_dir: Path | None = None,
        http_headers: dict[str, str | int] | None = None,
    ) -> None:
        super().__init__(
            app=self.standalone_app,
            root_components=[],
            path_prefix=path_prefix,
            web_modules_dir=web_modules_dir,
        )
        self.root_component = root_component
        self.extra_headers = http_headers or {}
        self.dispatcher_pattern = re.compile(f"^{self.dispatcher_path}?")

    async def standalone_app(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """ASGI app for ReactPy standalone mode."""
        if scope["type"] != "http":
            if scope["type"] != "lifespan":
                msg = (
                    "ReactPy app received unsupported request of type '%s' at path '%s'",
                    scope["type"],
                    scope["path"],
                )
                _logger.warning(msg)
                raise NotImplementedError(msg)
            return

        # Store the HTTP response in memory for performance
        if not self.cached_index_html:
            await self.process_index_html()

        # Return headers for all HTTP responses
        request_headers = dict(scope["headers"])
        response_headers: dict[str, str | int] = {
            "etag": self.etag,
            "last-modified": self.last_modified,
            "access-control-allow-origin": "*",
            "cache-control": "max-age=60, public",
            "content-length": len(self.cached_index_html),
            **self.extra_headers,
        }

        # Browser is asking for the headers
        if scope["method"] == "HEAD":
            return await http_response(
                scope["method"],
                send,
                200,
                "",
                content_type=b"text/html",
                headers=dict_to_byte_list(response_headers),
            )

        # Browser already has the content cached
        if request_headers.get(b"if-none-match") == self.etag.encode():
            response_headers.pop("content-length")
            return await http_response(
                scope["method"],
                send,
                304,
                "",
                content_type=b"text/html",
                headers=dict_to_byte_list(response_headers),
            )

        # Send the index.html
        await http_response(
            scope["method"],
            send,
            200,
            self.cached_index_html,
            content_type=b"text/html",
            headers=dict_to_byte_list(response_headers),
        )

    def match_dispatch_path(self, scope: dict) -> bool:
        """Check if the path matches the dispatcher path."""
        return str(scope["path"]).startswith(self.dispatcher_path)

    async def process_index_html(self):
        """Process the index.html file."""
        with open(self.index_html_path, encoding="utf-8") as file_handle:
            cached_index_html = file_handle.read()

        self.cached_index_html = find_and_replace(
            cached_index_html,
            {
                'from "index.ts"': f'from "{self.static_path}index.js"',
                "{path_prefix}": self.path_prefix,
                "{reconnect_interval}": "750",
                "{reconnect_max_interval}": "60000",
                "{reconnect_max_retries}": "150",
                "{reconnect_backoff_multiplier}": "1.25",
            },
        )

        self.etag = hashlib.md5(
            self.cached_index_html.encode(), usedforsecurity=False
        ).hexdigest()
        self.etag = f'"{self.etag}"'

        last_modified = os.stat(self.index_html_path).st_mtime
        self.last_modified = formatdate(last_modified, usegmt=True)


async def http_response(
    method: str,
    send: Callable[..., Coroutine],
    code: int,
    message: str,
    content_type: bytes = b"text/plain",
    headers: Sequence = (),
) -> None:
    """Send a simple response."""
    # Head requests don't need body content
    if method == "HEAD":
        await send(
            {
                "type": "http.response.start",
                "status": code,
                "headers": [*headers],
            }
        )
        await send({"type": "http.response.body"})
    else:
        await send(
            {
                "type": "http.response.start",
                "status": code,
                "headers": [(b"content-type", content_type), *headers],
            }
        )
        await send({"type": "http.response.body", "body": message.encode()})
