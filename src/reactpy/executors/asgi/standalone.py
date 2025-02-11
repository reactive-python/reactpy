from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import formatdate
from logging import getLogger
from typing import Callable, Literal, cast, overload

from asgi_tools import ResponseHTML
from typing_extensions import Unpack

from reactpy import html
from reactpy.executors.asgi.middleware import ReactPyMiddleware
from reactpy.executors.asgi.types import (
    AsgiApp,
    AsgiReceive,
    AsgiScope,
    AsgiSend,
    AsgiV3HttpApp,
    AsgiV3LifespanApp,
    AsgiV3WebsocketApp,
    AsgiWebsocketScope,
)
from reactpy.executors.utils import server_side_component_html, vdom_head_to_html
from reactpy.pyscript.utils import pyscript_setup_html
from reactpy.types import (
    PyScriptOptions,
    ReactPyConfig,
    RootComponentConstructor,
    VdomDict,
)
from reactpy.utils import html_to_vdom, import_dotted_path

_logger = getLogger(__name__)


class ReactPy(ReactPyMiddleware):
    multiple_root_components = False

    def __init__(
        self,
        root_component: RootComponentConstructor,
        *,
        http_headers: dict[str, str] | None = None,
        html_head: VdomDict | None = None,
        html_lang: str = "en",
        pyscript_setup: bool = False,
        pyscript_options: PyScriptOptions | None = None,
        **settings: Unpack[ReactPyConfig],
    ) -> None:
        """ReactPy's standalone ASGI application.

        Parameters:
            root_component: The root component to render. This app is typically a single page application.
            http_headers: Additional headers to include in the HTTP response for the base HTML document.
            html_head: Additional head elements to include in the HTML response.
            html_lang: The language of the HTML document.
            pyscript_setup: Whether to automatically load PyScript within your HTML head.
            pyscript_options: Options to configure PyScript behavior.
            settings: Global ReactPy configuration settings that affect behavior and performance.
        """
        super().__init__(app=ReactPyApp(self), root_components=[], **settings)
        self.root_component = root_component
        self.extra_headers = http_headers or {}
        self.dispatcher_pattern = re.compile(f"^{self.dispatcher_path}?")
        self.html_head = html_head or html.head()
        self.html_lang = html_lang

        if pyscript_setup:
            self.html_head.setdefault("children", [])
            pyscript_options = pyscript_options or {}
            extra_py = pyscript_options.get("extra_py", [])
            extra_js = pyscript_options.get("extra_js", {})
            config = pyscript_options.get("config", {})
            pyscript_head_vdom = html_to_vdom(
                pyscript_setup_html(extra_py, extra_js, config)
            )
            pyscript_head_vdom["tagName"] = ""
            self.html_head["children"].append(pyscript_head_vdom)  # type: ignore

    def match_dispatch_path(self, scope: AsgiWebsocketScope) -> bool:
        """Method override to remove `dotted_path` from the dispatcher URL."""
        return str(scope["path"]) == self.dispatcher_path

    def match_extra_paths(self, scope: AsgiScope) -> AsgiApp | None:
        """Method override to match user-provided HTTP/Websocket routes."""
        if scope["type"] == "lifespan":
            return self.extra_lifespan_app

        routing_dictionary = {}
        if scope["type"] == "http":
            routing_dictionary = self.extra_http_routes.items()

        if scope["type"] == "websocket":
            routing_dictionary = self.extra_ws_routes.items()

        return next(
            (
                app
                for route, app in routing_dictionary
                if re.match(route, scope["path"])
            ),
            None,
        )

    @overload
    def route(
        self,
        path: str,
        type: Literal["http"] = "http",
    ) -> Callable[[AsgiV3HttpApp | str], AsgiApp]: ...

    @overload
    def route(
        self,
        path: str,
        type: Literal["websocket"],
    ) -> Callable[[AsgiV3WebsocketApp | str], AsgiApp]: ...

    def route(
        self,
        path: str,
        type: Literal["http", "websocket"] = "http",
    ) -> (
        Callable[[AsgiV3HttpApp | str], AsgiApp]
        | Callable[[AsgiV3WebsocketApp | str], AsgiApp]
    ):
        """Interface that allows user to define their own HTTP/Websocket routes
        within the current ReactPy application.

        Parameters:
            path: The URL route to match, using regex format.
            type: The protocol to route for. Can be 'http' or 'websocket'.
        """

        def decorator(
            app: AsgiApp | str,
        ) -> AsgiApp:
            re_path = path
            if not re_path.startswith("^"):
                re_path = f"^{re_path}"
            if not re_path.endswith("$"):
                re_path = f"{re_path}$"

            asgi_app: AsgiApp = import_dotted_path(app) if isinstance(app, str) else app
            if type == "http":
                self.extra_http_routes[re_path] = cast(AsgiV3HttpApp, asgi_app)
            elif type == "websocket":
                self.extra_ws_routes[re_path] = cast(AsgiV3WebsocketApp, asgi_app)

            return asgi_app

        return decorator

    def lifespan(self, app: AsgiV3LifespanApp | str) -> None:
        """Interface that allows user to define their own lifespan app
        within the current ReactPy application.

        Parameters:
            app: The ASGI application to route to.
        """
        if self.extra_lifespan_app:
            raise ValueError("Only one lifespan app can be defined.")

        self.extra_lifespan_app = (
            import_dotted_path(app) if isinstance(app, str) else app
        )


@dataclass
class ReactPyApp:
    """ASGI app for ReactPy's standalone mode. This is utilized by `ReactPyMiddleware` as an alternative
    to a user provided ASGI app."""

    parent: ReactPy
    _index_html = ""
    _etag = ""
    _last_modified = ""

    async def __call__(
        self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend
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
        if not self._index_html:
            self.render_index_html()

        # Response headers for `index.html` responses
        request_headers = dict(scope["headers"])
        response_headers: dict[str, str] = {
            "etag": self._etag,
            "last-modified": self._last_modified,
            "access-control-allow-origin": "*",
            "cache-control": "max-age=60, public",
            "content-length": str(len(self._index_html)),
            "content-type": "text/html; charset=utf-8",
            **self.parent.extra_headers,
        }

        # Browser is asking for the headers
        if scope["method"] == "HEAD":
            response = ResponseHTML("", headers=response_headers)
            return await response(scope, receive, send)  # type: ignore

        # Browser already has the content cached
        if (
            request_headers.get(b"if-none-match") == self._etag.encode()
            or request_headers.get(b"if-modified-since") == self._last_modified.encode()
        ):
            response_headers.pop("content-length")
            response = ResponseHTML("", headers=response_headers, status_code=304)
            return await response(scope, receive, send)  # type: ignore

        # Send the index.html
        response = ResponseHTML(self._index_html, headers=response_headers)
        await response(scope, receive, send)  # type: ignore

    def render_index_html(self) -> None:
        """Process the index.html and store the results in this class."""
        self._index_html = (
            "<!doctype html>"
            f'<html lang="{self.parent.html_lang}">'
            f"{vdom_head_to_html(self.parent.html_head)}"
            "<body>"
            f"{server_side_component_html(element_id='app', class_='', component_path='')}"
            "</body>"
            "</html>"
        )
        self._etag = f'"{hashlib.md5(self._index_html.encode(), usedforsecurity=False).hexdigest()}"'
        self._last_modified = formatdate(
            datetime.now(tz=timezone.utc).timestamp(), usegmt=True
        )
