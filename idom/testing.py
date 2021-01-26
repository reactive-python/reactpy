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
)
from weakref import finalize

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


_Mount = TypeVar("_Mount")
_Server = TypeVar("_Server", bound=AnyRenderServer)


class ServerMountPoint(Generic[_Mount, _Server]):

    __slots__ = "server", "host", "port", "mount", "__weakref__"

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
    ):
        self.host = host
        self.port = port or find_available_port(host)
        self.mount, self.server = mount_and_server_constructor(
            server_type,
            self.host,
            self.port,
            server_config,
            run_kwargs,
            app,
            **other_options,
        )
        # stop server once mount is done being used
        finalize(self, self.server.stop)

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
