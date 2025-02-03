from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any, Callable
from urllib.parse import urlencode, urlunparse

import uvicorn
from asgiref import typing as asgi_types

from reactpy.asgi.middleware import ReactPyMiddleware
from reactpy.asgi.standalone import ReactPy
from reactpy.config import REACTPY_TESTS_DEFAULT_TIMEOUT
from reactpy.core.component import component
from reactpy.core.hooks import use_callback, use_effect, use_state
from reactpy.testing.logs import (
    LogAssertionError,
    capture_reactpy_logs,
    list_logged_exceptions,
)
from reactpy.testing.utils import find_available_port
from reactpy.types import ComponentConstructor, ReactPyConfig
from reactpy.utils import Ref


class BackendFixture:
    """A test fixture for running a server and imperatively displaying views

    This fixture is typically used alongside async web drivers like ``playwight``.

    Example:
        .. code-block::

            async with BackendFixture() as server:
                server.mount(MyComponent)
    """

    log_records: list[logging.LogRecord]
    _server_future: asyncio.Task[Any]
    _exit_stack = AsyncExitStack()

    def __init__(
        self,
        app: asgi_types.ASGIApplication | None = None,
        host: str = "127.0.0.1",
        port: int | None = None,
        timeout: float | None = None,
        reactpy_config: ReactPyConfig | None = None,
    ) -> None:
        self.host = host
        self.port = port or find_available_port(host)
        self.mount = mount_to_hotswap
        self.timeout = (
            REACTPY_TESTS_DEFAULT_TIMEOUT.current if timeout is None else timeout
        )
        if isinstance(app, (ReactPyMiddleware, ReactPy)):
            self._app = app
        elif app:
            self._app = ReactPyMiddleware(
                app,
                root_components=["reactpy.testing.backend.root_hotswap_component"],
                **(reactpy_config or {}),
            )
        else:
            self._app = ReactPy(
                root_hotswap_component,
                **(reactpy_config or {}),
            )
        self.webserver = uvicorn.Server(
            uvicorn.Config(
                app=self._app, host=self.host, port=self.port, loop="asyncio"
            )
        )

    def url(self, path: str = "", query: Any | None = None) -> str:
        """Return a URL string pointing to the host and point of the server

        Args:
            path: the path to a resource on the server
            query: a dictionary or list of query parameters
        """
        return urlunparse(
            [
                "http",
                f"{self.host}:{self.port}",
                path,
                "",
                urlencode(query or ()),
                "",
            ]
        )

    def list_logged_exceptions(
        self,
        pattern: str = "",
        types: type[Any] | tuple[type[Any], ...] = Exception,
        log_level: int = logging.ERROR,
        del_log_records: bool = True,
    ) -> list[BaseException]:
        """Return a list of logged exception matching the given criteria

        Args:
            log_level: The level of log to check
            exclude_exc_types: Any exception types to ignore
            del_log_records: Whether to delete the log records for yielded exceptions
        """
        return list_logged_exceptions(
            self.log_records,
            pattern,
            types,
            log_level,
            del_log_records,
        )

    async def __aenter__(self) -> BackendFixture:
        self._exit_stack = AsyncExitStack()
        self.log_records = self._exit_stack.enter_context(capture_reactpy_logs())

        # Wait for the server to start
        self.webserver.config.setup_event_loop()
        self.webserver_task = asyncio.create_task(self.webserver.serve())
        await asyncio.sleep(1)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._exit_stack.aclose()

        logged_errors = self.list_logged_exceptions(del_log_records=False)
        if logged_errors:  # nocov
            msg = "Unexpected logged exception"
            raise LogAssertionError(msg) from logged_errors[0]

        await self.webserver.shutdown()
        self.webserver_task.cancel()

    async def restart(self) -> None:
        """Restart the server"""
        await self.__aexit__(None, None, None)
        await self.__aenter__()


_MountFunc = Callable[["Callable[[], Any] | None"], None]


def _hotswap(update_on_change: bool = False) -> tuple[_MountFunc, ComponentConstructor]:
    """Swap out components from a layout on the fly.

    Since you can't change the component functions used to create a layout
    in an imperative manner, you can use ``hotswap`` to do this so
    long as you set things up ahead of time.

    Parameters:
        update_on_change: Whether or not all views of the layout should be updated on a swap.

    Example:
        .. code-block:: python

            import reactpy

            show, root = reactpy.hotswap()
            PerClientStateServer(root).run_in_thread("localhost", 8765)


            @reactpy.component
            def DivOne(self):
                return {"tagName": "div", "children": [1]}


            show(DivOne)

            # displaying the output now will show DivOne


            @reactpy.component
            def DivTwo(self):
                return {"tagName": "div", "children": [2]}


            show(DivTwo)

            # displaying the output now will show DivTwo
    """
    constructor_ref: Ref[Callable[[], Any]] = Ref(lambda: None)

    if update_on_change:
        set_constructor_callbacks: set[Callable[[Callable[[], Any]], None]] = set()

        @component
        def HotSwap() -> Any:
            # new displays will adopt the latest constructor and arguments
            constructor, _set_constructor = use_state(lambda: constructor_ref.current)
            set_constructor = use_callback(lambda new: _set_constructor(lambda _: new))

            def add_callback() -> Callable[[], None]:
                set_constructor_callbacks.add(set_constructor)
                return lambda: set_constructor_callbacks.remove(set_constructor)

            use_effect(add_callback)

            return constructor()

        def swap(constructor: Callable[[], Any] | None) -> None:
            constructor = constructor_ref.current = constructor or (lambda: None)

            for set_constructor in set_constructor_callbacks:
                set_constructor(constructor)

    else:

        @component
        def HotSwap() -> Any:
            return constructor_ref.current()

        def swap(constructor: Callable[[], Any] | None) -> None:
            constructor_ref.current = constructor or (lambda: None)

    return swap, HotSwap


mount_to_hotswap, root_hotswap_component = _hotswap()
