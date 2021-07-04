"""
Test Tooling
============
"""

import logging
import re
import shutil
from functools import wraps
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import urlencode, urlunparse
from weakref import ref

from selenium.webdriver import Chrome
from selenium.webdriver.remote.webdriver import WebDriver

from idom.config import IDOM_WED_MODULES_DIR
from idom.core.events import EventHandler
from idom.core.hooks import LifeCycleHook, current_hook
from idom.server.prefab import hotswap_server
from idom.server.proto import Server, ServerFactory
from idom.server.utils import find_available_port


__all__ = [
    "find_available_port",
    "create_simple_selenium_web_driver",
    "ServerMountPoint",
]


def create_simple_selenium_web_driver(
    driver_type: Type[WebDriver] = Chrome,
    driver_options: Optional[Any] = None,
    implicit_wait_timeout: float = 5.0,
    page_load_timeout: float = 5.0,
    window_size: Tuple[int, int] = (1080, 800),
) -> WebDriver:
    driver = driver_type(options=driver_options)

    driver.set_window_size(*window_size)
    driver.set_page_load_timeout(page_load_timeout)
    driver.implicitly_wait(implicit_wait_timeout)

    return driver


_Self = TypeVar("_Self", bound="ServerMountPoint[Any, Any]")
_Mount = TypeVar("_Mount")
_Server = TypeVar("_Server", bound=Server[Any])
_App = TypeVar("_App")
_Config = TypeVar("_Config")


class ServerMountPoint(Generic[_Mount, _Server]):
    """A context manager for imperatively mounting views to a render server when testing"""

    mount: _Mount
    server: _Server

    _log_handler: "_LogRecordCaptor"

    def __init__(
        self,
        server_type: Optional[ServerFactory[_App, _Config]] = None,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        server_config: Optional[_Config] = None,
        run_kwargs: Optional[Dict[str, Any]] = None,
        mount_and_server_constructor: "Callable[..., Tuple[_Mount, _Server]]" = hotswap_server,  # type: ignore
        app: Optional[_App] = None,
        **other_options: Any,
    ) -> None:
        self.host = host
        self.port = port or find_available_port(host)
        self._mount_and_server_constructor: "Callable[[], Tuple[_Mount, _Server]]" = (
            lambda: mount_and_server_constructor(
                server_type,
                self.host,
                self.port,
                server_config,
                run_kwargs,
                app,
                **other_options,
            )
        )

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

    def __enter__(self: _Self) -> _Self:
        self._log_handler = _LogRecordCaptor()
        logging.getLogger().addHandler(self._log_handler)
        self.mount, self.server = self._mount_and_server_constructor()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.server.stop()
        logging.getLogger().removeHandler(self._log_handler)
        del self.mount, self.server
        logged_errors = self.list_logged_exceptions(del_log_records=False)
        if logged_errors:  # pragma: no cover
            raise logged_errors[0]
        return None


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

            hooks = HookCatcher(index_by_kwarg="key")

            @idom.component
            @hooks.capture
            def MyComponent(key):
                ...

            ... # render the component

            # grab the last render of where MyComponent(key='some_key')
            hooks.index["some_key"]
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
        self._handler = EventHandler()

    @property
    def target(self) -> str:
        return self._handler.target

    def use(self, function: Callable[..., Any]) -> EventHandler:
        self._handler.clear()
        self._handler.add(function)
        return self._handler


def clear_idom_web_modules_dir() -> None:
    for path in IDOM_WED_MODULES_DIR.current.iterdir():
        shutil.rmtree(path) if path.is_dir() else path.unlink()
