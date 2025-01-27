import hashlib
import os
import re
from collections.abc import Coroutine
from dataclasses import dataclass
from email.utils import formatdate
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from typing_extensions import Unpack

from reactpy import html
from reactpy.asgi.middleware import ReactPyMiddleware
from reactpy.asgi.utils import (
    dict_to_byte_list,
    http_response,
    replace_many,
    vdom_head_to_html,
)
from reactpy.types import ReactPyConfig, RootComponentConstructor, VdomDict

_logger = getLogger(__name__)


class ReactPy(ReactPyMiddleware):
    multiple_root_components = False

    def __init__(
        self,
        root_component: RootComponentConstructor,
        *,
        http_headers: dict[str, str | int] | None = None,
        html_head: VdomDict | None = None,
        html_lang: str = "en",
        **settings: Unpack[ReactPyConfig],
    ) -> None:
        """TODO: Add docstring"""
        super().__init__(app=ReactPyApp(self), root_components=[], **settings)
        self.root_component = root_component
        self.extra_headers = http_headers or {}
        self.dispatcher_pattern = re.compile(f"^{self.dispatcher_path}?")
        self.html_head = html_head or html.head()
        self.html_lang = html_lang


@dataclass
class ReactPyApp:
    """ASGI app for ReactPy's standalone mode. This is utilized by `ReactPyMiddleware` as an alternative
    to a user provided ASGI app."""

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

        # Response headers for `index.html` responses
        request_headers = dict(scope["headers"])
        response_headers: dict[str, str | int] = {
            "etag": self._etag,
            "last-modified": self._last_modified,
            "access-control-allow-origin": "*",
            "cache-control": "max-age=60, public",
            "content-length": len(self._cached_index_html),
            "content-type": "text/html; charset=utf-8",
            **self.parent.extra_headers,
        }

        # Browser is asking for the headers
        if scope["method"] == "HEAD":
            return await http_response(
                send=send,
                method=scope["method"],
                headers=dict_to_byte_list(response_headers),
            )

        # Browser already has the content cached
        if request_headers.get(b"if-none-match") == self._etag.encode():
            response_headers.pop("content-length")
            return await http_response(
                send=send,
                method=scope["method"],
                code=304,
                headers=dict_to_byte_list(response_headers),
            )

        # Send the index.html
        await http_response(
            send=send,
            method=scope["method"],
            message=self._cached_index_html,
            headers=dict_to_byte_list(response_headers),
        )

    def match_dispatch_path(self, scope: dict) -> bool:
        """Method override to remove `dotted_path` from the dispatcher URL."""
        return str(scope["path"]) == self.parent.dispatcher_path

    def process_index_html(self) -> None:
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
