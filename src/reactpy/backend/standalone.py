import hashlib
import os
import re
from collections.abc import Coroutine, Sequence
from dataclasses import dataclass
from email.utils import formatdate
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from reactpy import html
from reactpy.backend.middleware import ReactPyMiddleware
from reactpy.backend.utils import dict_to_byte_list, replace_many, vdom_head_to_html
from reactpy.core.types import VdomDict
from reactpy.types import RootComponentConstructor

_logger = getLogger(__name__)


class ReactPy(ReactPyMiddleware):
    multiple_root_components = False

    def __init__(
        self,
        root_component: RootComponentConstructor,
        *,
        path_prefix: str = "/reactpy/",
        web_modules_dir: Path | None = None,
        http_headers: dict[str, str | int] | None = None,
        html_head: VdomDict | None = None,
        html_lang: str = "en",
    ) -> None:
        super().__init__(
            app=ReactPyApp(self),
            root_components=[],
            path_prefix=path_prefix,
            web_modules_dir=web_modules_dir,
        )
        self.root_component = root_component
        self.extra_headers = http_headers or {}
        self.dispatcher_pattern = re.compile(f"^{self.dispatcher_path}?")
        self.html_head = html_head or html.head()
        self.html_lang = html_lang


@dataclass
class ReactPyApp:
    parent: ReactPy
    _cached_index_html = ""
    _etag = ""
    _last_modified = ""
    _templates_dir = Path(__file__).parent.parent / "templates"
    _index_html_path = _templates_dir / "index.html"

    async def __call__(
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
        if not self._cached_index_html:
            self.process_index_html()

        # Return headers for all HTTP responses
        request_headers = dict(scope["headers"])
        response_headers: dict[str, str | int] = {
            "etag": self._etag,
            "last-modified": self._last_modified,
            "access-control-allow-origin": "*",
            "cache-control": "max-age=60, public",
            "content-length": len(self._cached_index_html),
            **self.parent.extra_headers,
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
        if request_headers.get(b"if-none-match") == self._etag.encode():
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
            self._cached_index_html,
            content_type=b"text/html",
            headers=dict_to_byte_list(response_headers),
        )

    def match_dispatch_path(self, scope: dict) -> bool:
        """Method override to remove `dotted_path` from the dispatcher URL."""
        return str(scope["path"]) == self.parent.dispatcher_path

    def process_index_html(self):
        """Process the index.html and store the results in memory."""
        with open(self._index_html_path, encoding="utf-8") as file_handle:
            cached_index_html = file_handle.read()

        self._cached_index_html = replace_many(
            cached_index_html,
            {
                'from "index.ts"': f'from "{self.parent.static_path}index.js"',
                '<html lang="en">': f'<html lang="{self.parent.html_lang}">',
                "<head></head>": vdom_head_to_html(self.parent.html_head),
                "{path_prefix}": self.parent.path_prefix,
                "{reconnect_interval}": "750",
                "{reconnect_max_interval}": "60000",
                "{reconnect_max_retries}": "150",
                "{reconnect_backoff_multiplier}": "1.25",
            },
        )

        self._etag = f'"{hashlib.md5(self._cached_index_html.encode(), usedforsecurity=False).hexdigest()}"'
        self._last_modified = formatdate(
            os.stat(self._index_html_path).st_mtime, usegmt=True
        )


async def http_response(
    method: str,
    send: Callable[..., Coroutine],
    code: int,
    message: str,
    content_type: bytes = b"text/plain",
    headers: Sequence = (),
) -> None:
    """Sends a HTTP response using the ASGI `send` API."""
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
