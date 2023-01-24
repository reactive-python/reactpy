from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any, Callable, Optional, Tuple, Type, Union
from urllib.parse import urlencode, urlunparse

from idom.backend import default as default_server
from idom.backend.types import BackendImplementation
from idom.backend.utils import find_available_port
from idom.config import IDOM_TESTING_DEFAULT_TIMEOUT
from idom.core.component import component
from idom.core.hooks import use_callback, use_effect, use_state
from idom.core.types import ComponentConstructor
from idom.utils import Ref

from .logs import LogAssertionError, capture_idom_logs, list_logged_exceptions


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
        port: Optional[int] = None,
        app: Any | None = None,
        implementation: BackendImplementation[Any] | None = None,
        options: Any | None = None,
        timeout: float | None = None,
    ) -> None:
        self.host = host
        self.port = port or find_available_port(host, allow_reuse_waiting_ports=False)
        self.mount, self._root_component = _hotswap()
        self.timeout = (
            IDOM_TESTING_DEFAULT_TIMEOUT.current if timeout is None else timeout
        )

        if app is not None:
            if implementation is None:
                raise ValueError(
                    "If an application instance its corresponding "
                    "server implementation must be provided too."
                )

        self._app = app
        self.implementation = implementation or default_server
        self._options = options

    @property
    def log_records(self) -> list[logging.LogRecord]:
        """A list of captured log records"""
        return self._records

    def url(self, path: str = "", query: Optional[Any] = None) -> str:
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
        types: Union[Type[Any], Tuple[Type[Any], ...]] = Exception,
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
        self._records = self._exit_stack.enter_context(capture_idom_logs())

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
            try:
                await asyncio.wait_for(server_future, timeout=self.timeout)
            except asyncio.CancelledError:
                pass

        self._exit_stack.push_async_callback(stop_server)

        try:
            await asyncio.wait_for(started.wait(), timeout=self.timeout)
        except Exception:  # pragma: no cover
            # see if we can await the future for a more helpful error
            await asyncio.wait_for(server_future, timeout=self.timeout)
            raise

        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self._exit_stack.aclose()

        self.mount(None)  # reset the view

        logged_errors = self.list_logged_exceptions(del_log_records=False)
        if logged_errors:  # pragma: no cover
            raise LogAssertionError("Unexpected logged exception") from logged_errors[0]

        return None


_MountFunc = Callable[["Callable[[], Any] | None"], None]


def _hotswap(update_on_change: bool = False) -> Tuple[_MountFunc, ComponentConstructor]:
    """Swap out components from a layout on the fly.

    Since you can't change the component functions used to create a layout
    in an imperative manner, you can use ``hotswap`` to do this so
    long as you set things up ahead of time.

    Parameters:
        update_on_change: Whether or not all views of the layout should be udpated on a swap.

    Example:
        .. code-block:: python

            import idom

            show, root = idom.hotswap()
            PerClientStateServer(root).run_in_thread("localhost", 8765)

            @idom.component
            def DivOne(self):
                return {"tagName": "div", "children": [1]}

            show(DivOne)

            # displaying the output now will show DivOne

            @idom.component
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

            return None

    else:

        @component
        def HotSwap() -> Any:
            return constructor_ref.current()

        def swap(constructor: Callable[[], Any] | None) -> None:
            constructor_ref.current = constructor or (lambda: None)
            return None

    return swap, HotSwap
