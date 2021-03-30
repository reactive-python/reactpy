import logging
import re
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

from selenium.webdriver import Chrome
from selenium.webdriver.remote.webdriver import WebDriver

from idom.server.base import AbstractRenderServer
from idom.server.prefab import hotswap_server
from idom.server.utils import find_available_port, find_builtin_server_type


__all__ = [
    "find_available_port",
    "create_simple_selenium_web_driver",
    "ServerMountPoint",
]


AnyRenderServer = AbstractRenderServer[Any, Any]


def create_simple_selenium_web_driver(
    driver_type: Type[WebDriver] = Chrome,
    driver_options: Optional[Any] = None,
    implicit_wait_timeout: float = 3.0,
    page_load_timeout: float = 3.0,
    window_size: Tuple[int, int] = (1080, 800),
) -> WebDriver:
    driver = driver_type(options=driver_options)

    driver.set_window_size(*window_size)
    driver.set_page_load_timeout(page_load_timeout)
    driver.implicitly_wait(implicit_wait_timeout)

    return driver


_Self = TypeVar("_Self", bound="ServerMountPoint[Any, Any]")
_Mount = TypeVar("_Mount")
_Server = TypeVar("_Server", bound=AnyRenderServer)


class ServerMountPoint(Generic[_Mount, _Server]):
    """A context manager for imperatively mounting views to a render server when testing"""

    mount: _Mount
    server: _Server

    _log_handler: "_LogRecordCaptor"

    def __init__(
        self,
        server_type: Type[_Server] = find_builtin_server_type("PerClientStateServer"),
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        server_config: Optional[Any] = None,
        run_kwargs: Optional[Dict[str, Any]] = None,
        mount_and_server_constructor: "Callable[..., Tuple[_Mount, _Server]]" = hotswap_server,  # type: ignore
        app: Optional[Any] = None,
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
            if record.levelno >= log_level and record.exc_info is not None:
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

    def handle(self, record: logging.LogRecord) -> None:
        self.records.append(record)
