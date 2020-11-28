import logging
import inspect
import time
from typing import Callable, Any, Type, Tuple, Iterator, Iterable, Union

import sanic
from loguru import logger
import pytest
from _pytest.logging import caplog as _caplog, LogCaptureFixture  # noqa
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

import pyalect.builtins.pytest  # noqa

import idom
from idom.client.manage import restore as restore_client
from idom.core import ElementConstructor, AbstractElement
from idom.server.prefab import hotswap_server, AbstractRenderServer
from idom.server.utils import find_available_port
from idom.server.sanic import PerClientStateServer


# Default is an error because we want to know whether we are setting the last
# error while testing. A refactor could miss the code path that catches serve
# errors.
default_error = NotImplementedError()


def pytest_collection_modifyitems(items: Iterable[Any]) -> None:
    for item in items:
        if isinstance(item, pytest.Function):
            if inspect.iscoroutinefunction(item.function):
                item.add_marker(pytest.mark.asyncio)
        if "driver" in item.fixturenames:
            item.add_marker("slow")


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--headless",
        dest="headless",
        action="store_true",
        help="Whether to run browser tests in headless mode.",
    )
    parser.addoption(
        "--dirty-client",
        dest="dirty_client",
        action="store_true",
        help="Whether to refresh the client before and after testing.",
    )


@pytest.fixture(autouse=True)
def caplog(_caplog: LogCaptureFixture) -> Iterator[LogCaptureFixture]:
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    handler_id = logger.add(PropogateHandler(), format="{message}")
    yield _caplog
    logger.remove(handler_id)
    assert not _caplog.record_tuples


@pytest.fixture
def display(
    driver: Chrome,
    driver_get: Callable[[str], None],
    server: AbstractRenderServer,
    mount: Callable[..., None],
    host: str,
    port: int,
    display_id: idom.Ref[int],
    last_server_error: idom.Ref[Exception],
) -> Iterator[Callable[[Union[ElementConstructor, AbstractElement], str], None]]:
    """A function for displaying an element using the current web driver."""

    def display(
        element: Union[ElementConstructor, AbstractElement],
        query: str = "",
        check_mount: bool = True,
    ):
        d_id = display_id.current
        display_id.current += 1
        display_attrs = {"id": f"display-{d_id}"}
        element_constructor = element if callable(element) else lambda: element
        mount(lambda: idom.html.div(display_attrs, element_constructor()))
        driver_get(query)
        if check_mount:
            # Ensure element was actually mounted.
            driver.find_element_by_id(f"display-{d_id}")

    try:
        yield display
    finally:
        last_error = last_server_error.current
        if last_error is default_error:
            msg = f"The server {server} never ran or did not set the 'last_server_error' fixture."
            raise NotImplementedError(msg)
        elif last_error is not None:
            raise last_error


@pytest.fixture
def driver_get(driver: Chrome, server_url: str) -> Callable[[str], None]:
    """Navigate the driver to an IDOM server at the given host and port.

    The ``query`` parameter is typically used to specify a ``view_id`` when a
    ``multiview()`` elemement has been mounted to the layout.
    """

    def get(query: str = "") -> None:
        driver.get(f"{server_url}/client/index.html?{query}")

    return get


@pytest.fixture
def driver_wait(driver: Chrome, driver_timeout: float) -> WebDriverWait:
    """A :class:`WebDriverWait` object for the current web driver"""
    return WebDriverWait(driver, driver_timeout)


@pytest.fixture(scope="session")
def display_id() -> idom.Ref[int]:
    return idom.Ref(0)


@pytest.fixture(scope="module")
def driver(create_driver: Callable[[], Chrome]) -> Chrome:
    """A Selenium web driver"""
    return create_driver()


@pytest.fixture(scope="module")
def create_driver(pytestconfig: Config, fresh_client: None, driver_timeout: float):
    """A Selenium web driver"""
    created_drivers = []

    def create():
        chrome_options = Options()

        if pytestconfig.option.headless:
            chrome_options.headless = True

        driver = Chrome(options=chrome_options)

        driver.set_window_size(1080, 800)
        driver.set_page_load_timeout(driver_timeout)
        driver.implicitly_wait(driver_timeout)

        created_drivers.append(driver)

        return driver

    yield create

    for d in created_drivers:
        d.quit()


@pytest.fixture(scope="session")
def driver_timeout() -> float:
    """How the web driver will wait for a condition (e.g. page load, element lookup)"""
    return 3.0


@pytest.fixture(scope="module")
def mount(
    mount_and_server: Tuple[Callable[..., None], AbstractRenderServer]
) -> Callable[..., None]:
    """A function for mounting an element to the IDOM server's layout"""
    return mount_and_server[0]


@pytest.fixture(scope="module")
def server(
    mount_and_server: Tuple[Callable[..., None], AbstractRenderServer]
) -> Iterator[AbstractRenderServer]:
    """An IDOM server"""
    server = mount_and_server[1]
    time.sleep(1)  # wait for server to start
    yield server
    server.stop()


@pytest.fixture(scope="module")
def mount_and_server(
    application: sanic.Sanic,
    fixturized_server_type: Type[AbstractRenderServer],
    host: str,
    port: int,
    last_server_error: idom.Ref[Exception],
) -> Tuple[Callable[..., None], AbstractRenderServer]:
    """An IDOM layout mount function and server as a tuple

    The ``mount`` and ``server`` fixtures use this.
    """

    mount, server = hotswap_server(
        fixturized_server_type,
        host,
        port,
        server_options={"cors": True, "last_server_error": last_server_error},
        run_options={},
        sync_views=False,
        app=application,
    )
    return mount, server


@pytest.fixture(scope="module")
def application():
    return sanic.Sanic()


@pytest.fixture(scope="module")
def fixturized_server_type(server_type):
    class ServerSavesLastError(server_type):
        """A per-client-state server that updates the ``last_server_error`` fixture"""

        async def _run_dispatcher(self, *args, **kwargs):
            self._config["last_server_error"].current = None
            try:
                await super()._run_dispatcher(*args, **kwargs)
            except Exception as e:
                self._config["last_server_error"].current = e

    return ServerSavesLastError


@pytest.fixture(scope="module")
def server_type() -> Type[AbstractRenderServer]:
    """The type of server the ``mount_and_server`` fixture will use to initialize a server"""
    return PerClientStateServer


@pytest.fixture(scope="module")
def server_url(host, port):
    return f"http://{host}:{port}"


@pytest.fixture(scope="session")
def host() -> str:
    """The hostname for the IDOM server setup by ``mount_and_server``"""
    return "127.0.0.1"


@pytest.fixture(scope="module")
def port(host: str) -> int:
    """The port for the IDOM server setup by ``mount_and_server``"""
    return find_available_port(host)


@pytest.fixture(scope="session")
def last_server_error():
    """A ``Ref`` containing the last server error. This must be populated by ``server_type``"""
    return idom.Ref(default_error)


@pytest.fixture(autouse=True)
def _clean_last_server_error(last_server_error) -> Iterator[None]:
    last_server_error.current = default_error
    yield


@pytest.fixture(scope="session")
def fresh_client(pytestconfig: Config) -> Iterator[None]:
    """Restore the client's state before and after testing

    For faster test runs set ``--dirty-client`` at the CLI. Test coverage and
    breakages may occur if this is set. Further the client is not cleaned up
    after testing and may effect usage of IDOM beyond the scope of the tests.
    """
    if not pytestconfig.option.dirty_client:
        restore_client()
        yield
        restore_client()
    else:
        yield
