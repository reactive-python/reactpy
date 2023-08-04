from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack, suppress
from types import TracebackType
from typing import Any, Callable
from urllib.parse import urlencode, urlunparse

from reactpy.backend import default as default_server
from reactpy.backend.types import BackendType
from reactpy.backend.utils import find_available_port
from reactpy.config import REACTPY_TESTING_DEFAULT_TIMEOUT
from reactpy.core.component import component
from reactpy.core.hooks import use_callback, use_effect, use_state
from reactpy.core.types import ComponentConstructor
from reactpy.testing.logs import (
    LogAssertionError,
    capture_reactpy_logs,
    list_logged_exceptions,
)
from reactpy.utils import Ref


class BackendFixture:
    """A test fixture for running a server and imperatively displaying views

    This fixture is typically used alongside async web drivers like ``playwight``.

    Example:
        .. code-block::

            async with BackendFixture() as server:
                server.mount(MyComponent)
    """

    _records: list[logging.LogRecord]
    _server_future: asyncio.Task[Any]
    _exit_stack = AsyncExitStack()

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int | None = None,
        app: Any | None = None,
        implementation: BackendType[Any] | None = None,
        options: Any | None = None,
        timeout: float | None = None,
    ) -> None:
        self.host = host
        self.port = port or find_available_port(host)
        self.mount, self._root_component = _hotswap()
        self.timeout = (
            REACTPY_TESTING_DEFAULT_TIMEOUT.current if timeout is None else timeout
        )

        if app is not None and implementation is None:
            msg = "If an application instance its corresponding server implementation must be provided too."
            raise ValueError(msg)

        self._app = app
        self.implementation = implementation or default_server
        self._options = options

    @property
    def log_records(self) -> list[logging.LogRecord]:
        """A list of captured log records"""
        return self._records

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
        self._records = self._exit_stack.enter_context(capture_reactpy_logs())

        app = self._app or self.implementation.create_development_app()
        self.implementation.configure(app, self._root_component, self._options)

        started = asyncio.Event()
        server_future = asyncio.create_task(
            self.implementation.serve_development_app(
                app, self.host, self.port, started
            )
        )

        async def stop_server() -> None:
            server_future.cancel()
            with suppress(asyncio.CancelledError):
                await asyncio.wait_for(server_future, timeout=self.timeout)

        self._exit_stack.push_async_callback(stop_server)

        try:
            await asyncio.wait_for(started.wait(), timeout=self.timeout)
        except Exception:  # nocov
            # see if we can await the future for a more helpful error
            await asyncio.wait_for(server_future, timeout=self.timeout)
            raise

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._exit_stack.aclose()

        self.mount(None)  # reset the view

        logged_errors = self.list_logged_exceptions(del_log_records=False)
        if logged_errors:  # nocov
            msg = "Unexpected logged exception"
            raise LogAssertionError(msg) from logged_errors[0]


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
