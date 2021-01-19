from urllib.parse import urlunparse, urlencode
from contextlib import contextmanager
from typing import (
    Callable,
    Tuple,
    Iterator,
    Type,
    Optional,
    Any,
    Dict,
    Generic,
    TypeVar,
)
from weakref import finalize

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver import Chrome

from idom.server.utils import find_builtin_server_type
from idom.server.base import AbstractRenderServer
from idom.server.prefab import hotswap_server
from idom.server.utils import find_available_port
from idom.utils import Ref


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


_Mount = TypeVar("_Mount")
_Server = TypeVar("_Server", bound=AnyRenderServer)


class ServerMountPoint(Generic[_Mount, _Server]):

    __slots__ = "server", "host", "port", "_mount", "__weakref__"

    def __init__(
        self,
        server_type: Type[_Server] = find_builtin_server_type("PerClientStateServer"),
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        server_config: Optional[Any] = None,
        run_kwargs: Optional[Dict[str, Any]] = None,
        mount_and_server_constructor: "Callable[..., Tuple[_Mount, _Server]]" = hotswap_server,
        app: Optional[Any] = None,
        **other_options: Any,
    ):
        self.host = host
        self.port = port or find_available_port(host)
        self._mount, server = mount_and_server_constructor(
            (
                server_type
                if issubclass(server_type, _RenderServerWithLastError)
                else type(
                    server_type.__name__,
                    (_RenderServerWithLastError, server_type),
                    {"last_server_error_for_idom_testing": Ref(None)},
                )
            ),
            self.host,
            self.port,
            server_config,
            run_kwargs,
            app,
            **other_options,
        )
        self.server = server
        # stop server once mount is done being used
        finalize(self, server.stop)

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

    @contextmanager
    def open_mount_function(self) -> Iterator[_Mount]:
        self.server.last_server_error_for_idom_testing.current = None
        try:
            yield self._mount
        finally:
            if self.server.last_server_error_for_idom_testing.current is not None:
                raise self.server.last_server_error_for_idom_testing.current  # pragma: no cover


class _RenderServerWithLastError(AnyRenderServer):
    """A server that updates the ``last_server_error`` fixture"""

    last_server_error_for_idom_testing: Ref[Optional[Exception]]

    async def _run_dispatcher(self, *args: Any, **kwargs: Any) -> None:
        self.last_server_error_for_idom_testing.current = None
        try:
            await super()._run_dispatcher(*args, **kwargs)
        except Exception as e:
            self.last_server_error_for_idom_testing.current = e
