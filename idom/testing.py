import re
import logging
from urllib.parse import urlunparse, urlencode
from typing import (
    Callable,
    Tuple,
    Type,
    Optional,
    Any,
    Dict,
    Generic,
    TypeVar,
    List,
    Union,
)
from types import TracebackType

from loguru import logger
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver import Chrome

from idom.server.utils import find_builtin_server_type
from idom.server.base import AbstractRenderServer
from idom.server.prefab import hotswap_server
from idom.server.utils import find_available_port


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
    _loguru_handler_id: int

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

    def assert_logged_exception(
        self,
        error_type: Type[Exception],
        error_pattern: str,
        clear_after: bool = True,
    ) -> None:
        """Assert that a given error type and message were logged"""
        try:
            re_pattern = re.compile(error_pattern)
            for record in self.log_records:
                if record.exc_info is not None:
                    error = record.exc_info[1]
                    if isinstance(error, error_type) and re_pattern.search(str(error)):
                        break
            else:  # pragma: no cover
                assert False, f"did not raise {error_type} matching {error_pattern!r}"
        finally:
            if clear_after:
                self.log_records.clear()

    def raise_first_logged_exception(
        self,
        exclude_exc_types: Union[Type[Exception], Tuple[Type[Exception], ...]] = (),
    ) -> None:
        """Raise the first logged exception (if any)

        Args:
            exclude_exc_types: Any exception types to ignore
        """
        for record in self._log_handler.records:
            if record.exc_info is not None:
                error = record.exc_info[1]
                if error is not None and not isinstance(error, exclude_exc_types):
                    raise error

    def url(self, path: str = "", query: Optional[Any] = None) -> str:
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

    def __enter__(self: _Self) -> _Self:
        self._log_handler = _LogRecordCaptor()
        logging.getLogger().addHandler(self._log_handler)
        self._loguru_handler_id = logger.add(self._log_handler, format="{message}")
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
        logger.remove(self._loguru_handler_id)

        self.raise_first_logged_exception()

        return None


class _LogRecordCaptor(logging.NullHandler):
    def __init__(self) -> None:
        self.records: List[logging.LogRecord] = []
        super().__init__()

    def handle(self, record: logging.LogRecord) -> None:
        self.records.append(record)
