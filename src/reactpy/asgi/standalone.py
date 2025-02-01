from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import formatdate
from logging import getLogger

from asgiref import typing as asgi_types
from typing_extensions import Unpack

from reactpy import html
from reactpy.asgi.middleware import ReactPyMiddleware
from reactpy.asgi.utils import dict_to_byte_list, http_response, vdom_head_to_html
from reactpy.types import ReactPyConfig, RootComponentConstructor, VdomDict
from reactpy.utils import render_mount_template

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
        """ReactPy's standalone ASGI application.

        Parameters:
            root_component: The root component to render. This component is assumed to be a single page application.
            http_headers: Additional headers to include in the HTTP response for the base HTML document.
            html_head: Additional head elements to include in the HTML response.
            html_lang: The language of the HTML document.
            settings: Global ReactPy configuration settings that affect behavior and performance.
        """
        super().__init__(app=ReactPyApp(self), root_components=[], **settings)
        self.root_component = root_component
        self.extra_headers = http_headers or {}
        self.dispatcher_pattern = re.compile(f"^{self.dispatcher_path}?")
        self.html_head = html_head or html.head()
        self.html_lang = html_lang

    def match_dispatch_path(self, scope: asgi_types.WebSocketScope) -> bool:
        """Method override to remove `dotted_path` from the dispatcher URL."""
        return str(scope["path"]) == self.dispatcher_path


@dataclass
class ReactPyApp:
    """ASGI app for ReactPy's standalone mode. This is utilized by `ReactPyMiddleware` as an alternative
    to a user provided ASGI app."""

    parent: ReactPy
    _cached_index_html = ""
    _etag = ""
    _last_modified = ""

    async def __call__(
        self,
        scope: asgi_types.Scope,
        receive: asgi_types.ASGIReceiveCallable,
        send: asgi_types.ASGISendCallable,
    ) -> None:
        if scope["type"] != "http":  # pragma: no cover
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
        if (
            request_headers.get(b"if-none-match") == self._etag.encode()
            or request_headers.get(b"if-modified-since") == self._last_modified.encode()
        ):
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

    def process_index_html(self) -> None:
        """Process the index.html and store the results in memory."""
        self._cached_index_html = (
            "<!doctype html>"
            f'<html lang="{self.parent.html_lang}">'
            f"{vdom_head_to_html(self.parent.html_head)}"
            "<body>"
            f"{render_mount_template('app', '', '')}"
            "</body>"
            "</html>"
        )

        self._etag = f'"{hashlib.md5(self._cached_index_html.encode(), usedforsecurity=False).hexdigest()}"'
        self._last_modified = formatdate(
            datetime.now(tz=timezone.utc).timestamp(), usegmt=True
        )
