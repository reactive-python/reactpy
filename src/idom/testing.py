from __future__ import annotations

import asyncio
import logging
import re
import shutil
from contextlib import contextmanager
from functools import wraps
from traceback import format_exception
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    NoReturn,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import urlencode, urlunparse
from uuid import uuid4
from weakref import ref

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.common.options import BaseOptions
from selenium.webdriver.remote.webdriver import WebDriver

from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.events import EventHandler, to_event_handler_function
from idom.core.hooks import LifeCycleHook, current_hook
from idom.server import any as any_server
from idom.server.types import ServerImplementation
from idom.server.utils import find_available_port
from idom.widgets import MountFunc, hotswap

from .log import ROOT_LOGGER


__all__ = [
    "find_available_port",
    "create_simple_selenium_web_driver",
    "ServerMountPoint",
]


def create_simple_selenium_web_driver(
    driver_type: Type[WebDriver] = Chrome,
    driver_options: BaseOptions = ChromeOptions(),
    implicit_wait_timeout: float = 10.0,
    page_load_timeout: float = 5.0,
    window_size: Tuple[int, int] = (1080, 800),
) -> WebDriver:
    driver = driver_type(options=driver_options)

    driver.set_window_size(*window_size)
    driver.set_page_load_timeout(page_load_timeout)
    driver.implicitly_wait(implicit_wait_timeout)

    return driver


_Self = TypeVar("_Self", bound="ServerMountPoint")


class ServerMountPoint:
    """A context manager for imperatively mounting views to a render server when testing"""

    _log_handler: "_LogRecordCaptor"
    _server_future: asyncio.Task

    def __init__(
        self,
        server_implementation: ServerImplementation = any_server,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        update_on_mount: bool = False,
    ) -> None:
        self.server_implementation = server_implementation
        self.host = host
        self.port = port or find_available_port(host, allow_reuse_waiting_ports=False)
        self._update_on_mount = update_on_mount

    @property
    def log_records(self) -> List[logging.LogRecord]:
        """A list of captured log records"""
        return self._log_handler.records

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

    async def __aenter__(self: _Self) -> _Self:
        self.mount, root_component = hotswap(self._update_on_mount)

        self._log_handler = _LogRecordCaptor()
        logging.getLogger().addHandler(self._log_handler)
        app = self.server_implementation.create_development_app()
        self.server_implementation.configure(app, root_component)

        started = asyncio.Event()
        self._server_future = asyncio.ensure_future(
            self.server_implementation.serve_development_app(
                app, self.host, self.port, started
            )
        )

        await asyncio.wait_for(started.wait(), timeout=3)

        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self._server_future.cancel()

        logging.getLogger().removeHandler(self._log_handler)
        logged_errors = self.list_logged_exceptions(del_log_records=False)
        if logged_errors:  # pragma: no cover
            raise logged_errors[0]

        return None


class LogAssertionError(AssertionError):
    """An assertion error raised in relation to log messages."""


@contextmanager
def assert_idom_logged(
    match_message: str = "",
    error_type: type[Exception] | None = None,
    match_error: str = "",
    clear_matched_records: bool = False,
) -> Iterator[None]:
    """Assert that IDOM produced a log matching the described message or error.

    Args:
        match_message: Must match a logged message.
        error_type: Checks the type of logged exceptions.
        match_error: Must match an error message.
        clear_matched_records: Whether to remove logged records that match.
    """
    message_pattern = re.compile(match_message)
    error_pattern = re.compile(match_error)

    try:
        with capture_idom_logs(yield_existing=clear_matched_records) as log_records:
            yield None
    except Exception:
        raise
    else:
        found = False
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
                found = True
                if clear_matched_records:
                    log_records.remove(record)

        if not found:  # pragma: no cover
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
    clear_matched_records: bool = False,
) -> Iterator[None]:
    """Assert the inverse of :func:`assert_idom_logged`"""
    try:
        with assert_idom_logged(
            match_message, error_type, match_error, clear_matched_records
        ):
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
def capture_idom_logs(
    yield_existing: bool = False,
) -> Iterator[list[logging.LogRecord]]:
    """Capture logs from IDOM

    Parameters:
        yield_existing:
            If already inside an existing capture context yield the same list of logs.
            This is useful if you need to mutate the list of logs to affect behavior in
            the outer context.
    """
    if yield_existing:
        for handler in reversed(ROOT_LOGGER.handlers):
            if isinstance(handler, _LogRecordCaptor):
                yield handler.records
                return None

    handler = _LogRecordCaptor()
    original_level = ROOT_LOGGER.level

    ROOT_LOGGER.setLevel(logging.DEBUG)
    ROOT_LOGGER.addHandler(handler)
    try:
        yield handler.records
    finally:
        ROOT_LOGGER.removeHandler(handler)
        ROOT_LOGGER.setLevel(original_level)


class _LogRecordCaptor(logging.NullHandler):
    def __init__(self) -> None:
        self.records: List[logging.LogRecord] = []
        super().__init__()

    def handle(self, record: logging.LogRecord) -> bool:
        self.records.append(record)
        return True


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
