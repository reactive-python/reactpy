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
from asgiref import typing as asgi_types
from asgiref.compatibility import guarantee_single_callable
from servestatic import ServeStaticASGI
from typing_extensions import Unpack

from reactpy import config
from reactpy.asgi.utils import check_path, import_components, process_settings
from reactpy.core.hooks import ConnectionContext
from reactpy.core.layout import Layout
from reactpy.core.serve import serve_layout
from reactpy.types import Connection, Location, ReactPyConfig, RootComponentConstructor

_logger = logging.getLogger(__name__)


class ReactPyMiddleware:
    _asgi_single_callable: bool = True
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
        self.js_modules_pattern = re.compile(f"^{self.web_modules_path}.*")
        self.static_pattern = re.compile(f"^{self.static_path}.*")

        # Component attributes
        self.user_app: asgi_types.ASGI3Application = guarantee_single_callable(app)  # type: ignore
        self.root_components = import_components(root_components)

        # Directory attributes
        self.web_modules_dir = config.REACTPY_WEB_MODULES_DIR.current
        self.static_dir = Path(__file__).parent.parent / "static"

        # Validate the configuration
        reason = check_path(self.path_prefix)
        if reason:
            raise ValueError(f"Invalid `path_prefix`. {reason}")
        if not self.web_modules_dir.exists():
            raise ValueError(
                f"Web modules directory {self.web_modules_dir} does not exist."
            )

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

        # Serve the user's application
        await self.user_app(scope, receive, send)

    def match_dispatch_path(self, scope: asgi_types.WebSocketScope) -> bool:
        return bool(re.match(self.dispatcher_pattern, scope["path"]))

    def match_static_path(self, scope: asgi_types.HTTPScope) -> bool:
        return bool(re.match(self.static_pattern, scope["path"]))

    def match_web_modules_path(self, scope: asgi_types.HTTPScope) -> bool:
        return bool(re.match(self.js_modules_pattern, scope["path"]))


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
        dispatcher: asyncio.Task[Any] | None = None
        recv_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        # Start a loop that handles ASGI websocket events
        while True:
            event = await receive()
            if event["type"] == "websocket.connect":
                await send(
                    {"type": "websocket.accept", "subprotocol": None, "headers": []}
                )
                dispatcher = asyncio.create_task(
                    self.run_dispatcher(scope, receive, send, recv_queue)
                )

            elif event["type"] == "websocket.disconnect":
                if dispatcher:
                    dispatcher.cancel()
                break

            elif event["type"] == "websocket.receive" and event["text"]:
                queue_put_func = recv_queue.put(orjson.loads(event["text"]))
                await queue_put_func

    async def run_dispatcher(
        self,
        scope: asgi_types.WebSocketScope,
        receive: asgi_types.ASGIReceiveCallable,
        send: asgi_types.ASGISendCallable,
        recv_queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        """Asyncio background task that renders and transmits layout updates of ReactPy components."""
        try:
            # Determine component to serve by analyzing the URL and/or class parameters.
            if self.parent.multiple_root_components:
                url_match = re.match(self.parent.dispatcher_pattern, scope["path"])
                if not url_match:
                    raise RuntimeError("Could not find component in URL path.")
                dotted_path = url_match["dotted_path"]
                if dotted_path not in self.parent.root_components:
                    raise RuntimeError(
                        f"Attempting to use an unregistered root component {dotted_path}."
                    )
                component = self.parent.root_components[dotted_path]
            elif self.parent.root_component:
                component = self.parent.root_component
            else:
                raise RuntimeError("No root component provided.")

            # Create a connection object by analyzing the websocket's query string.
            ws_query_string = urllib.parse.parse_qs(
                scope["query_string"].decode(), strict_parsing=True
            )
            connection = Connection(
                scope=scope,
                location=Location(
                    path=ws_query_string.get("http_pathname", [""])[0],
                    query_string=ws_query_string.get("http_query_string", [""])[0],
                ),
                carrier=self,
            )

            # Start the ReactPy component rendering loop
            await serve_layout(
                Layout(ConnectionContext(component(), value=connection)),
                lambda msg: send(
                    {
                        "type": "websocket.send",
                        "text": orjson.dumps(msg).decode(),
                        "bytes": None,
                    }
                ),
                recv_queue.get,  # type: ignore
            )

        # Manually log exceptions since this function is running in a separate asyncio task.
        except Exception as error:
            await asyncio.to_thread(_logger.error, f"{error}\n{traceback.format_exc()}")


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
                self.parent.user_app,
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
                self.parent.user_app,
                root=self.parent.web_modules_dir,
                prefix=self.parent.web_modules_path,
                autorefresh=True,
            )

        await self._static_file_server(scope, receive, send)
