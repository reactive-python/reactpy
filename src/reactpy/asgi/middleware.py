from __future__ import annotations

import asyncio
import logging
import re
import traceback
import urllib.parse
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import orjson
from asgi_tools import ResponseText, ResponseWebSocket
from asgiref import typing as asgi_types
from asgiref.compatibility import guarantee_single_callable
from servestatic import ServeStaticASGI
from typing_extensions import Unpack

from reactpy import config
from reactpy.asgi.utils import check_path, import_components, process_settings
from reactpy.core.hooks import ConnectionContext
from reactpy.core.layout import Layout
from reactpy.core.serve import serve_layout
from reactpy.types import (
    AsgiApp,
    AsgiHttpApp,
    AsgiLifespanApp,
    AsgiWebsocketApp,
    AsgiWebsocketReceive,
    AsgiWebsocketSend,
    Connection,
    Location,
    ReactPyConfig,
    RootComponentConstructor,
)

_logger = logging.getLogger(__name__)


class ReactPyMiddleware:
    root_component: RootComponentConstructor | None = None
    root_components: dict[str, RootComponentConstructor]
    multiple_root_components: bool = True

    def __init__(
        self,
        app: asgi_types.ASGIApplication,
        root_components: Iterable[str],
        **settings: Unpack[ReactPyConfig],
    ) -> None:
        """Configure the ASGI app. Anything initialized in this method will be shared across all future requests.

        Parameters:
            app: The ASGI application to serve when the request does not match a ReactPy route.
            root_components:
                A list, set, or tuple containing the dotted path of your root components. This dotted path
                must be valid to Python's import system.
            settings: Global ReactPy configuration settings that affect behavior and performance.
        """
        # Validate the configuration
        if "path_prefix" in settings:
            reason = check_path(settings["path_prefix"])
            if reason:
                raise ValueError(
                    f'Invalid `path_prefix` of "{settings["path_prefix"]}". {reason}'
                )
        if "web_modules_dir" in settings and not settings["web_modules_dir"].exists():
            raise ValueError(
                f'Web modules directory "{settings["web_modules_dir"]}" does not exist.'
            )

        # Process global settings
        process_settings(settings)

        # URL path attributes
        self.path_prefix = config.REACTPY_PATH_PREFIX.current
        self.dispatcher_path = self.path_prefix
        self.web_modules_path = f"{self.path_prefix}modules/"
        self.static_path = f"{self.path_prefix}static/"
        self.dispatcher_pattern = re.compile(
            f"^{self.dispatcher_path}(?P<dotted_path>[a-zA-Z0-9_.]+)/$"
        )

        # User defined ASGI apps
        self.extra_http_routes: dict[str, AsgiHttpApp] = {}
        self.extra_ws_routes: dict[str, AsgiWebsocketApp] = {}
        self.extra_lifespan_app: AsgiLifespanApp | None = None

        # Component attributes
        self.asgi_app: asgi_types.ASGI3Application = guarantee_single_callable(app)  # type: ignore
        self.root_components = import_components(root_components)

        # Directory attributes
        self.web_modules_dir = config.REACTPY_WEB_MODULES_DIR.current
        self.static_dir = Path(__file__).parent.parent / "static"

        # Initialize the sub-applications
        self.component_dispatch_app = ComponentDispatchApp(parent=self)
        self.static_file_app = StaticFileApp(parent=self)
        self.web_modules_app = WebModuleApp(parent=self)

    async def __call__(
        self,
        scope: asgi_types.Scope,
        receive: asgi_types.ASGIReceiveCallable,
        send: asgi_types.ASGISendCallable,
    ) -> None:
        """The ASGI entrypoint that determines whether ReactPy should route the
        request to ourselves or to the user application."""
        # URL routing for the ReactPy renderer
        if scope["type"] == "websocket" and self.match_dispatch_path(scope):
            return await self.component_dispatch_app(scope, receive, send)

        # URL routing for ReactPy static files
        if scope["type"] == "http" and self.match_static_path(scope):
            return await self.static_file_app(scope, receive, send)

        # URL routing for ReactPy web modules
        if scope["type"] == "http" and self.match_web_modules_path(scope):
            return await self.web_modules_app(scope, receive, send)

        # URL routing for user-defined routes
        matched_app = self.match_extra_paths(scope)
        if matched_app:
            return await matched_app(scope, receive, send)  # type: ignore

        # Serve the user's application
        await self.asgi_app(scope, receive, send)

    def match_dispatch_path(self, scope: asgi_types.WebSocketScope) -> bool:
        return bool(re.match(self.dispatcher_pattern, scope["path"]))

    def match_static_path(self, scope: asgi_types.HTTPScope) -> bool:
        return scope["path"].startswith(self.static_path)

    def match_web_modules_path(self, scope: asgi_types.HTTPScope) -> bool:
        return scope["path"].startswith(self.web_modules_path)

    def match_extra_paths(self, scope: asgi_types.Scope) -> AsgiApp | None:
        # Custom defined routes are unused by default to encourage users to handle
        # routing within their root ASGI application.
        return None


@dataclass
class ComponentDispatchApp:
    parent: ReactPyMiddleware

    async def __call__(
        self,
        scope: asgi_types.WebSocketScope,
        receive: asgi_types.ASGIReceiveCallable,
        send: asgi_types.ASGISendCallable,
    ) -> None:
        """ASGI app for rendering ReactPy Python components."""
        # Start a loop that handles ASGI websocket events
        async with ReactPyWebsocket(scope, receive, send, parent=self.parent) as ws:  # type: ignore
            while True:
                # Wait for the webserver to notify us of a new event
                event: dict[str, Any] = await ws.receive(raw=True)  # type: ignore

                # If the event is a `receive` event, parse the message and send it to the rendering queue
                if event["type"] == "websocket.receive":
                    msg: dict[str, str] = orjson.loads(event["text"])
                    if msg.get("type") == "layout-event":
                        await ws.rendering_queue.put(msg)
                    else:  # pragma: no cover
                        await asyncio.to_thread(
                            _logger.warning, f"Unknown message type: {msg.get('type')}"
                        )

                # If the event is a `disconnect` event, break the rendering loop and close the connection
                elif event["type"] == "websocket.disconnect":
                    break


class ReactPyWebsocket(ResponseWebSocket):
    def __init__(
        self,
        scope: asgi_types.WebSocketScope,
        receive: AsgiWebsocketReceive,
        send: AsgiWebsocketSend,
        parent: ReactPyMiddleware,
    ) -> None:
        super().__init__(scope=scope, receive=receive, send=send)  # type: ignore
        self.scope = scope
        self.parent = parent
        self.rendering_queue: asyncio.Queue[dict[str, str]] = asyncio.Queue()
        self.dispatcher: asyncio.Task[Any] | None = None

    async def __aenter__(self) -> ReactPyWebsocket:
        self.dispatcher = asyncio.create_task(self.run_dispatcher())
        return await super().__aenter__()  # type: ignore

    async def __aexit__(self, *_: Any) -> None:
        if self.dispatcher:
            self.dispatcher.cancel()
        await super().__aexit__()  # type: ignore

    async def run_dispatcher(self) -> None:
        """Async background task that renders ReactPy components over a websocket."""
        try:
            # Determine component to serve by analyzing the URL and/or class parameters.
            if self.parent.multiple_root_components:
                url_match = re.match(self.parent.dispatcher_pattern, self.scope["path"])
                if not url_match:  # pragma: no cover
                    raise RuntimeError("Could not find component in URL path.")
                dotted_path = url_match["dotted_path"]
                if dotted_path not in self.parent.root_components:
                    raise RuntimeError(
                        f"Attempting to use an unregistered root component {dotted_path}."
                    )
                component = self.parent.root_components[dotted_path]
            elif self.parent.root_component:
                component = self.parent.root_component
            else:  # pragma: no cover
                raise RuntimeError("No root component provided.")

            # Create a connection object by analyzing the websocket's query string.
            ws_query_string = urllib.parse.parse_qs(
                self.scope["query_string"].decode(), strict_parsing=True
            )
            connection = Connection(
                scope=self.scope,
                location=Location(
                    path=ws_query_string.get("http_pathname", [""])[0],
                    query_string=ws_query_string.get("http_query_string", [""])[0],
                ),
                carrier=self,
            )

            # Start the ReactPy component rendering loop
            await serve_layout(
                Layout(ConnectionContext(component(), value=connection)),
                self.send_json,
                self.rendering_queue.get,  # type: ignore
            )

        # Manually log exceptions since this function is running in a separate asyncio task.
        except Exception as error:
            await asyncio.to_thread(_logger.error, f"{error}\n{traceback.format_exc()}")

    async def send_json(self, data: Any) -> None:
        return await self._send(
            {"type": "websocket.send", "text": orjson.dumps(data).decode()}
        )


@dataclass
class StaticFileApp:
    parent: ReactPyMiddleware
    _static_file_server: ServeStaticASGI | None = None

    async def __call__(
        self,
        scope: asgi_types.HTTPScope,
        receive: asgi_types.ASGIReceiveCallable,
        send: asgi_types.ASGISendCallable,
    ) -> None:
        """ASGI app for ReactPy static files."""
        if not self._static_file_server:
            self._static_file_server = ServeStaticASGI(
                Error404App(),
                root=self.parent.static_dir,
                prefix=self.parent.static_path,
            )

        await self._static_file_server(scope, receive, send)


@dataclass
class WebModuleApp:
    parent: ReactPyMiddleware
    _static_file_server: ServeStaticASGI | None = None

    async def __call__(
        self,
        scope: asgi_types.HTTPScope,
        receive: asgi_types.ASGIReceiveCallable,
        send: asgi_types.ASGISendCallable,
    ) -> None:
        """ASGI app for ReactPy web modules."""
        if not self._static_file_server:
            self._static_file_server = ServeStaticASGI(
                Error404App(),
                root=self.parent.web_modules_dir,
                prefix=self.parent.web_modules_path,
                autorefresh=True,
            )

        await self._static_file_server(scope, receive, send)


class Error404App:
    async def __call__(self, scope, receive, send):
        response = ResponseText("Resource not found on this server.", status_code=404)
        await response(scope, receive, send)
