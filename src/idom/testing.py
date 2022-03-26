from __future__ import annotations

import asyncio
import logging
import operator
import re
import shutil
import time
from contextlib import AsyncExitStack, ExitStack, contextmanager
from functools import partial, wraps
from inspect import isawaitable, iscoroutinefunction
from traceback import format_exception
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Generic,
    Iterator,
    List,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import urlencode, urlunparse
from uuid import uuid4
from weakref import ref

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from typing_extensions import ParamSpec

from idom import html
from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.events import EventHandler, to_event_handler_function
from idom.core.hooks import LifeCycleHook, current_hook
from idom.server import default as default_server
from idom.server.types import ServerImplementation
from idom.server.utils import find_available_port
from idom.types import RootComponentConstructor
from idom.widgets import hotswap

from .log import ROOT_LOGGER


__all__ = [
    "find_available_port",
    "create_simple_selenium_web_driver",
    "ServerFixture",
]

_Self = TypeVar("_Self")


def assert_same_items(left: Sequence[Any], right: Sequence[Any]) -> None:
    """Check that two unordered sequences are equal (only works if reprs are equal)"""
    sorted_left = list(sorted(left, key=repr))
    sorted_right = list(sorted(right, key=repr))
    assert sorted_left == sorted_right


_P = ParamSpec("_P")
_R = TypeVar("_R")
_DEFAULT_TIMEOUT = 3.0


class poll(Generic[_R]):
    """Wait until the result of an sync or async function meets some condition"""

    def __init__(
        self,
        function: Callable[_P, Awaitable[_R] | _R],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None:
        if iscoroutinefunction(function):

            async def until(
                condition: Callable[[_R], bool], timeout: float = _DEFAULT_TIMEOUT
            ) -> None:
                started_at = time.time()
                while True:
                    result = await function(*args, **kwargs)
                    if condition(result):
                        break
                    elif (time.time() - started_at) > timeout:
                        raise TimeoutError(
                            f"Condition not met within {timeout} "
                            f"seconds - last value was {result!r}"
                        )

        else:

            def until(
                condition: Callable[[_R], bool] | Any, timeout: float = _DEFAULT_TIMEOUT
            ) -> None:
                started_at = time.time()
                while True:
                    result = function(*args, **kwargs)
                    if condition(result):
                        break
                    elif (time.time() - started_at) > timeout:
                        raise TimeoutError(
                            f"Condition not met within {timeout} "
                            f"seconds - last value was {result!r}"
                        )

        self.until: Callable[[Callable[[_R], bool]], Any] = until
        """Check that the coroutines result meets a condition within the timeout"""

    def until_is(self, right: Any, timeout: float = _DEFAULT_TIMEOUT) -> Any:
        """Wait until the result is identical to the given value"""
        return self.until(lambda left: left is right, timeout)

    def until_equals(self, right: Any, timeout: float = _DEFAULT_TIMEOUT) -> Any:
        """Wait until the result is equal to the given value"""
        return self.until(lambda left: left == right, timeout)


class DisplayFixture:
    """A fixture for running web-based tests using ``playwright``"""

    _exit_stack: AsyncExitStack

    def __init__(
        self,
        server: ServerFixture | None = None,
        driver: Browser | BrowserContext | Page | None = None,
    ) -> None:
        if server is not None:
            self.server = server
        if driver is not None:
            if isinstance(driver, Page):
                self.page = driver
            else:
                self._browser = driver
        self._next_view_id = 0

    async def show(
        self,
        component: RootComponentConstructor,
        query: dict[str, Any] | None = None,
    ) -> None:
        self._next_view_id += 1
        view_id = f"display-{self._next_view_id}"
        self.server.mount(lambda: html.div({"id": view_id}, component()))

        await self.page.goto(self.server.url(query=query))
        await self.page.wait_for_selector(f"#{view_id}", state="attached")

    async def __aenter__(self) -> DisplayFixture:
        es = self._exit_stack = AsyncExitStack()

        if not hasattr(self, "page"):
            if not hasattr(self, "_browser"):
                pw = await es.enter_async_context(async_playwright())
                browser = await pw.chromium.launch()
            else:
                browser = self._browser
            self.page = await browser.new_page()

        if not hasattr(self, "server"):
            self.server = ServerFixture()
            await es.enter_async_context(self.server)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.server.mount(None)
        await self._exit_stack.aclose()


class ServerFixture:
    """A test fixture for running a server and imperatively displaying views

    This fixture is typically used alongside async web drivers like ``playwight``.

    Example:
        .. code-block::

            async with ServerFixture() as server:
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
        implementation: ServerImplementation[Any] = default_server,
    ) -> None:
        self.host = host
        self.port = port or find_available_port(host, allow_reuse_waiting_ports=False)
        self.mount, self._root_component = hotswap()

        if app is not None:
            if implementation is None:
                raise ValueError(
                    "If an application instance its corresponding "
                    "server implementation must be provided too."
                )

        self._app = app
        self.implementation = implementation

    @property
    def log_records(self) -> List[logging.LogRecord]:
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
    ) -> List[BaseException]:
        """Return a list of logged exception matching the given criteria

        Args:
            log_level: The level of log to check
            exclude_exc_types: Any exception types to ignore
            del_log_records: Whether to delete the log records for yielded exceptions
        """
        found: List[BaseException] = []
        compiled_pattern = re.compile(pattern)
        for index, record in enumerate(self.log_records):
            if record.levelno >= log_level and record.exc_info:
                error = record.exc_info[1]
                if (
                    error is not None
                    and isinstance(error, types)
                    and compiled_pattern.search(str(error))
                ):
                    if del_log_records:
                        del self.log_records[index - len(found)]
                    found.append(error)
        return found

    async def __aenter__(self) -> ServerFixture:
        self._exit_stack = AsyncExitStack()
        self._records = self._exit_stack.enter_context(capture_idom_logs())

        app = self._app or self.implementation.create_development_app()
        self.implementation.configure(app, self._root_component)

        started = asyncio.Event()
        server_future = asyncio.create_task(
            self.implementation.serve_development_app(
                app, self.host, self.port, started
            )
        )

        async def stop_server():
            server_future.cancel()
            try:
                await asyncio.wait_for(server_future, timeout=3)
            except asyncio.CancelledError:
                pass

        self._exit_stack.push_async_callback(stop_server)

        try:
            await asyncio.wait_for(started.wait(), timeout=3)
        except Exception:
            # see if we can await the future for a more helpful error
            await asyncio.wait_for(server_future, timeout=3)
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


class LogAssertionError(AssertionError):
    """An assertion error raised in relation to log messages."""


@contextmanager
def assert_idom_logged(
    match_message: str = "",
    error_type: type[Exception] | None = None,
    match_error: str = "",
    clear_after: bool = True,
) -> Iterator[None]:
    """Assert that IDOM produced a log matching the described message or error.

    Args:
        match_message: Must match a logged message.
        error_type: Checks the type of logged exceptions.
        match_error: Must match an error message.
        clear_after: Whether to remove logged records that match.
    """
    message_pattern = re.compile(match_message)
    error_pattern = re.compile(match_error)

    with capture_idom_logs(clear_after=clear_after) as log_records:
        try:
            yield None
        except Exception:
            raise
        else:
            for record in list(log_records):
                if (
                    # record message matches
                    message_pattern.findall(record.getMessage())
                    # error type matches
                    and (
                        error_type is None
                        or (
                            record.exc_info is not None
                            and record.exc_info[0] is not None
                            and issubclass(record.exc_info[0], error_type)
                        )
                    )
                    # error message pattern matches
                    and (
                        not match_error
                        or (
                            record.exc_info is not None
                            and error_pattern.findall(
                                "".join(format_exception(*record.exc_info))
                            )
                        )
                    )
                ):
                    break
            else:  # pragma: no cover
                _raise_log_message_error(
                    "Could not find a log record matching the given",
                    match_message,
                    error_type,
                    match_error,
                )


@contextmanager
def assert_idom_did_not_log(
    match_message: str = "",
    error_type: type[Exception] | None = None,
    match_error: str = "",
    clear_after: bool = True,
) -> Iterator[None]:
    """Assert the inverse of :func:`assert_idom_logged`"""
    try:
        with assert_idom_logged(match_message, error_type, match_error, clear_after):
            yield None
    except LogAssertionError:
        pass
    else:
        _raise_log_message_error(
            "Did find a log record matching the given",
            match_message,
            error_type,
            match_error,
        )


def _raise_log_message_error(
    prefix: str,
    match_message: str = "",
    error_type: type[Exception] | None = None,
    match_error: str = "",
) -> NoReturn:
    conditions = []
    if match_message:
        conditions.append(f"log message pattern {match_message!r}")
    if error_type:
        conditions.append(f"exception type {error_type}")
    if match_error:
        conditions.append(f"error message pattern {match_error!r}")
    raise LogAssertionError(prefix + " " + " and ".join(conditions))


@contextmanager
def capture_idom_logs(clear_after: bool = True) -> Iterator[list[logging.LogRecord]]:
    """Capture logs from IDOM

    Args:
        clear_after:
            Clear any records which were produced in this context when exiting.
    """
    original_level = ROOT_LOGGER.level
    ROOT_LOGGER.setLevel(logging.DEBUG)
    try:
        if _LOG_RECORD_CAPTOR in ROOT_LOGGER.handlers:
            start_index = len(_LOG_RECORD_CAPTOR.records)
            try:
                yield _LOG_RECORD_CAPTOR.records
            finally:
                end_index = len(_LOG_RECORD_CAPTOR.records)
                _LOG_RECORD_CAPTOR.records[start_index:end_index] = []
            return None

        ROOT_LOGGER.addHandler(_LOG_RECORD_CAPTOR)
        try:
            yield _LOG_RECORD_CAPTOR.records
        finally:
            ROOT_LOGGER.removeHandler(_LOG_RECORD_CAPTOR)
            _LOG_RECORD_CAPTOR.records.clear()
    finally:
        ROOT_LOGGER.setLevel(original_level)


class HookCatcher:
    """Utility for capturing a LifeCycleHook from a component

    Example:
        .. code-block::

            hooks = HookCatcher(index_by_kwarg="thing")

            @idom.component
            @hooks.capture
            def MyComponent(thing):
                ...

            ...  # render the component

            # grab the last render of where MyComponent(thing='something')
            hooks.index["something"]
            # or grab the hook from the component's last render
            hooks.latest

        After the first render of ``MyComponent`` the ``HookCatcher`` will have
        captured the component's ``LifeCycleHook``.
    """

    latest: LifeCycleHook

    def __init__(self, index_by_kwarg: Optional[str] = None):
        self.index_by_kwarg = index_by_kwarg
        self.index: Dict[Any, LifeCycleHook] = {}

    def capture(self, render_function: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator for capturing a ``LifeCycleHook`` on each render of a component"""

        # The render function holds a reference to `self` and, via the `LifeCycleHook`,
        # the component. Some tests check whether components are garbage collected, thus
        # we must use a `ref` here to ensure these checks pass once the catcher itself
        # has been collected.
        self_ref = ref(self)

        @wraps(render_function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self = self_ref()
            assert self is not None, "Hook catcher has been garbage collected"

            hook = current_hook()
            if self.index_by_kwarg is not None:
                self.index[kwargs[self.index_by_kwarg]] = hook
            self.latest = hook
            return render_function(*args, **kwargs)

        return wrapper


class StaticEventHandler:
    """Utility for capturing the target of one event handler

    Example:
        .. code-block::

            static_handler = StaticEventHandler()

            @idom.component
            def MyComponent():
                state, set_state = idom.hooks.use_state(0)
                handler = static_handler.use(lambda event: set_state(state + 1))
                return idom.html.button({"onClick": handler}, "Click me!")

            # gives the target ID for onClick where from the last render of MyComponent
            static_handlers.target

        If you need to capture event handlers from different instances of a component
        the you should create multiple ``StaticEventHandler`` instances.

        .. code-block::

            static_handlers_by_key = {
                "first": StaticEventHandler(),
                "second": StaticEventHandler(),
            }

            @idom.component
            def Parent():
                return idom.html.div(Child(key="first"), Child(key="second"))

            @idom.component
            def Child(key):
                state, set_state = idom.hooks.use_state(0)
                handler = static_handlers_by_key[key].use(lambda event: set_state(state + 1))
                return idom.html.button({"onClick": handler}, "Click me!")

            # grab the individual targets for each instance above
            first_target = static_handlers_by_key["first"].target
            second_target = static_handlers_by_key["second"].target
    """

    def __init__(self) -> None:
        self.target = uuid4().hex

    def use(
        self,
        function: Callable[..., Any],
        stop_propagation: bool = False,
        prevent_default: bool = False,
    ) -> EventHandler:
        return EventHandler(
            to_event_handler_function(function),
            stop_propagation,
            prevent_default,
            self.target,
        )


def clear_idom_web_modules_dir() -> None:
    for path in IDOM_WEB_MODULES_DIR.current.iterdir():
        shutil.rmtree(path) if path.is_dir() else path.unlink()


class _LogRecordCaptor(logging.NullHandler):
    def __init__(self) -> None:
        self.records: List[logging.LogRecord] = []
        super().__init__()

    def handle(self, record: logging.LogRecord) -> bool:
        self.records.append(record)
        return True


_LOG_RECORD_CAPTOR = _LogRecordCaptor()
