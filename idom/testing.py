from idom.server.base import AbstractRenderServer
import time
from contextlib import contextmanager, AbstractContextManager
from typing import Callable, Tuple, Iterator, Type, Optional, Union, Any

from sanic import Sanic
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

import idom
from idom.core.element import AbstractElement, ElementConstructor
from idom.server.sanic import PerClientStateServer
from idom.widgets.utils import MultiViewMount
from idom.server.prefab import hotswap_server, multiview_server
from idom.server.utils import find_available_port
from idom.utils import Ref


MountFunc = Callable[[Union[ElementConstructor, AbstractElement], str], None]
MountFuncContext = Callable[[], "AbstractContextManager[MountFunc]"]


@contextmanager
def open_selenium_driver_and_mount(
    headless: bool, driver_timeout: float = 3.0, wait_for_server_start: float = 1.0
) -> Iterator[Tuple[Chrome, MountFuncContext]]:
    host = "127.0.0.1"
    port = find_available_port(host)
    server_url = f"http://{host}:{port}"

    with open_selenium_web_driver(
        headless=headless,
        page_load_timeout=driver_timeout,
        implicit_wait_timeout=driver_timeout,
    ) as driver:
        mount, server = create_hotswap_mount_and_server(
            server_type=PerClientStateServer, host=host, port=port
        )
        time.sleep(wait_for_server_start)
        yield (
            driver,
            lambda: open_selenium_mount_context(driver, server, server_url, mount),
        )


def create_selenium_get_page_function(
    driver: WebDriver, server_url: str
) -> Callable[[str], None]:
    def get_view(query: str = "") -> None:
        """Navigate the driver to an IDOM server at the given host and port.

        The ``query`` parameter is typically used to specify a ``view_id`` when a
        ``multiview()`` elemement has been mounted to the layout.
        """
        driver.get(f"{server_url}/client/index.html?{query}")

    return get_view


@contextmanager
def open_selenium_mount_context(
    driver: WebDriver,
    server: AbstractRenderServer[Any, Any],
    server_url: str,
    element_mount_function: Callable[..., None],
) -> Iterator[MountFunc]:
    display_id = Ref(0)

    get_page = create_selenium_get_page_function(driver, server_url)

    def mount_function(
        element: Union[Callable[[], Any], AbstractElement],
        query: str = "",
        check_mount: bool = True,
    ) -> None:
        d_id = display_id.current
        display_id.current += 1
        display_attrs = {"id": f"display-{d_id}"}
        element_constructor = element if callable(element) else lambda: element
        element_mount_function(
            lambda: idom.html.div(display_attrs, element_constructor())
        )

        get_page(query)

        if check_mount:
            # Ensure element was actually mounted.
            driver.find_element_by_id(f"display-{d_id}")

        return None

    server.last_server_error_for_idom_testing.current = None  # type: ignore
    try:
        yield mount_function
    finally:
        if server.last_server_error_for_idom_testing.current is not None:  # type: ignore
            raise server.last_server_error_for_idom_testing.current


def create_multiview_mount_and_server(
    server_type: Type[AbstractRenderServer[Any, Any]],
    host: str,
    port: int,
    debug: bool = False,
    app: Optional[Sanic] = None,
) -> Tuple[MultiViewMount, AbstractRenderServer[Any, Any]]:
    return multiview_server(
        create_server_type_for_testing(server_type),
        host,
        port,
        server_options={"cors": True},
        run_options={"debug": debug},
        app=app,
    )


def create_hotswap_mount_and_server(
    server_type: Type[AbstractRenderServer[Any, Any]],
    host: str,
    port: int,
    sync_views: bool = False,
    debug: bool = False,
    app: Optional[Sanic] = None,
) -> Tuple[Callable[..., None], AbstractRenderServer[Any, Any]]:

    return hotswap_server(
        create_server_type_for_testing(server_type),
        host,
        port,
        server_options={"cors": True},
        run_options={"debug": debug},
        sync_views=sync_views,
        app=app,
    )


def create_server_type_for_testing(
    server_type: Type[AbstractRenderServer[Any, Any]],
) -> Type[AbstractRenderServer[Any, Any]]:
    return (
        server_type
        if issubclass(server_type, RenderServerWithLastError)
        else type(
            server_type.__name__,
            (RenderServerWithLastError, server_type),
            {"last_server_error_for_idom_testing": Ref(None)},
        )
    )


@contextmanager
def open_selenium_web_driver(
    headless: bool,
    implicit_wait_timeout: float = 3.0,
    page_load_timeout: float = 3.0,
    window_size: Tuple[int, int] = (1080, 800),
) -> Iterator[Chrome]:
    options = Options()
    options.headless = headless

    driver = Chrome(options=options)

    driver.set_window_size(*window_size)
    driver.set_page_load_timeout(page_load_timeout)
    driver.implicitly_wait(implicit_wait_timeout)

    try:
        yield driver
    finally:
        driver.quit()


class RenderServerWithLastError(AbstractRenderServer[Any, Any]):
    """A server that updates the ``last_server_error`` fixture"""

    last_server_error_for_idom_testing: Ref[Optional[Exception]]

    async def _run_dispatcher(self, *args: Any, **kwargs: Any) -> None:
        self.last_server_error_for_idom_testing.current = None
        try:
            await super()._run_dispatcher(*args, **kwargs)
        except Exception as e:
            self.last_server_error_for_idom_testing.current = e
