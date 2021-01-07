from urllib.parse import urlunparse, urlencode
from contextlib import contextmanager, AbstractContextManager
from idom.core.element import ElementConstructor
from typing import (
    Callable,
    NamedTuple,
    Tuple,
    Iterator,
    Type,
    Optional,
    Union,
    Any,
    Dict,
)

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver import Chrome

from idom.server.base import AbstractRenderServer
from idom.server.sanic import PerClientStateServer
from idom.server.prefab import hotswap_server
from idom.server.utils import find_available_port
from idom.utils import Ref


MountType = Union[Callable[[ElementConstructor], None], Any]
MountContext = Callable[[], "AbstractContextManager[MountType]"]
AnyAbstractRenderServer = AbstractRenderServer[Any, Any]


def server_base_url(host: str, port: int, path: str = "", query: Optional[Any] = None):
    return urlunparse(["http", f"{host}:{port}", path, "", urlencode(query or ()), ""])


class MountAndServer(NamedTuple):
    mount: MountContext
    server: AnyAbstractRenderServer


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


def create_mount_and_server(
    server_type: Type[AnyAbstractRenderServer] = PerClientStateServer,
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    server_config: Optional[Any] = None,
    run_kwargs: Optional[Dict[str, Any]] = None,
    mount_and_server_constructor: Callable[..., Any] = hotswap_server,
    app: Optional[Any] = None,
    **other_options: Any,
) -> MountAndServer:
    mount, server = mount_and_server_constructor(
        (
            server_type
            if issubclass(server_type, _RenderServerWithLastError)
            else type(
                server_type.__name__,
                (_RenderServerWithLastError, server_type),
                {"last_server_error_for_idom_testing": Ref(None)},
            )
        ),
        host,
        port or find_available_port(),
        server_config,
        run_kwargs,
        app,
        **other_options,
    )

    assert isinstance(server, _RenderServerWithLastError)

    @contextmanager
    def mount_context() -> Iterator[MountType]:
        server.last_server_error_for_idom_testing.current = None
        try:
            yield mount
        finally:
            if server.last_server_error_for_idom_testing.current is not None:
                raise server.last_server_error_for_idom_testing.current

    return MountAndServer(mount_context, server)


class _RenderServerWithLastError(AnyAbstractRenderServer):
    """A server that updates the ``last_server_error`` fixture"""

    last_server_error_for_idom_testing: Ref[Optional[Exception]]

    async def _run_dispatcher(self, *args: Any, **kwargs: Any) -> None:
        self.last_server_error_for_idom_testing.current = None
        try:
            await super()._run_dispatcher(*args, **kwargs)
        except Exception as e:
            self.last_server_error_for_idom_testing.current = e
