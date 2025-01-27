from __future__ import annotations

import asyncio
import logging
import re
import traceback
import urllib.parse
from collections.abc import Coroutine, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import orjson
from asgiref.compatibility import guarantee_single_callable
from servestatic import ServeStaticASGI

from reactpy.backend.types import Connection, Location
from reactpy.backend.utils import check_path, import_components, normalize_url_path
from reactpy.config import REACTPY_WEB_MODULES_DIR
from reactpy.core.hooks import ConnectionContext
from reactpy.core.layout import Layout
from reactpy.core.serve import serve_layout
from reactpy.types import RootComponentConstructor

_logger = logging.getLogger(__name__)


class ReactPyMiddleware:
    _asgi_single_callable: bool = True
    root_component: RootComponentConstructor | None = None
    root_components: dict[str, RootComponentConstructor]
    multiple_root_components: bool = True

    def __init__(
        self,
        app: Callable[..., Coroutine],
        root_components: Iterable[str],
        *,
        # TODO: Add a setting attribute to this class. Or maybe just put a shit ton of kwargs here. Or add a **kwargs that resolves to a TypedDict?
        path_prefix: str = "reactpy/",
        web_modules_dir: Path | None = None,
    ) -> None:
        """Configure the ASGI app. Anything initialized in this method will be shared across all future requests."""
        # URL path attributes
        self.path_prefix = normalize_url_path(path_prefix)
        self.dispatcher_path = f"/{self.path_prefix}/"
        self.web_modules_path = f"/{self.path_prefix}/modules/"
        self.static_path = f"/{self.path_prefix}/static/"
        self.dispatcher_pattern = re.compile(
            f"^{self.dispatcher_path}(?P<dotted_path>[^/]+)/?"
        )
        self.js_modules_pattern = re.compile(f"^{self.web_modules_path}.*")
        self.static_pattern = re.compile(f"^{self.static_path}.*")

        # Component attributes
        self.user_app = guarantee_single_callable(app)
        self.root_components = import_components(root_components)

        # Directory attributes
        self.web_modules_dir = web_modules_dir or REACTPY_WEB_MODULES_DIR.current
        self.static_dir = Path(__file__).parent.parent / "static"
        if self.web_modules_dir != REACTPY_WEB_MODULES_DIR.current:
            REACTPY_WEB_MODULES_DIR.set_current(self.web_modules_dir)

        # Sub-applications
        self.component_dispatch_app = ComponentDispatchApp(parent=self)
        self.static_file_app = StaticFileApp(parent=self)
        self.web_modules_app = WebModuleApp(parent=self)

        # Validate the configuration
        reason = check_path(path_prefix)
        if reason:
            raise ValueError(f"Invalid `path_prefix`. {reason}")

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
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

    def match_dispatch_path(self, scope: dict) -> bool:
        return bool(re.match(self.dispatcher_pattern, scope["path"]))

    def match_static_path(self, scope: dict) -> bool:
        return bool(re.match(self.static_pattern, scope["path"]))

    def match_web_modules_path(self, scope: dict) -> bool:
        return bool(re.match(self.js_modules_pattern, scope["path"]))


@dataclass
class ComponentDispatchApp:
    parent: ReactPyMiddleware

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """ASGI app for rendering ReactPy Python components."""
        dispatcher: asyncio.Task | None = None
        recv_queue: asyncio.Queue = asyncio.Queue()

        # Start a loop that handles ASGI websocket events
        while True:
            event = await receive()
            if event["type"] == "websocket.connect":
                await send({"type": "websocket.accept"})
                dispatcher = asyncio.create_task(
                    self.run_dispatcher(scope, receive, send, recv_queue)
                )

            if event["type"] == "websocket.disconnect":
                if dispatcher:
                    dispatcher.cancel()
                break

            if event["type"] == "websocket.receive":
                queue_put_func = recv_queue.put(orjson.loads(event["text"]))
                await queue_put_func

    async def run_dispatcher(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
        recv_queue: asyncio.Queue,
    ) -> None:
        # Get the component from the URL.
        try:
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

            parsed_url = urllib.parse.urlparse(scope["path"])

            await serve_layout(
                Layout(  # type: ignore
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
                self.send_json(send),
                recv_queue.get,
            )
        except Exception as error:
            await asyncio.to_thread(_logger.error, f"{error}\n{traceback.format_exc()}")

    @staticmethod
    def send_json(send: Callable) -> Callable[..., Coroutine]:
        """Use orjson to send JSON over an ASGI websocket."""

        async def _send_json(value: Any) -> None:
            await send({"type": "websocket.send", "text": orjson.dumps(value).decode()})

        return _send_json


@dataclass
class StaticFileApp:
    parent: ReactPyMiddleware
    _static_file_server: ServeStaticASGI | None = None

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """ASGI app for ReactPy static files."""
        # If no static directory is configured, serve the user's application
        if not self.parent.static_dir:
            await asyncio.to_thread(
                _logger.info,
                "Tried to serve static file without a configured directory.",
            )
            return await self.parent.user_app(scope, receive, send)

        if not self._static_file_server:
            self._static_file_server = ServeStaticASGI(
                self.parent.user_app,
                root=self.parent.static_dir,
                prefix=self.parent.static_path,
            )

        return await self._static_file_server(scope, receive, send)


@dataclass
class WebModuleApp:
    parent: ReactPyMiddleware
    _static_file_server: ServeStaticASGI | None = None

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """ASGI app for ReactPy web modules."""
        if not self.parent.web_modules_dir:
            await asyncio.to_thread(
                _logger.info,
                "Tried to serve web module without a configured directory.",
            )
            return await self.parent.user_app(scope, receive, send)

        if not self._static_file_server:
            self._static_file_server = ServeStaticASGI(
                self.parent.user_app,
                root=self.parent.web_modules_dir,
                prefix=self.parent.web_modules_path,
                autorefresh=True,
            )

        return await self._static_file_server(scope, receive, send)
