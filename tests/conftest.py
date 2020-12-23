import logging
import inspect
import time
from contextlib import ExitStack
from typing import Callable, Any, Type, Tuple, Iterator, Iterable, Union

import sanic
from loguru import logger
import pytest
from _pytest.logging import caplog as _caplog, LogCaptureFixture  # noqa
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait

import pyalect.builtins.pytest  # noqa

import idom
from idom.client import manage as manage_client
from idom.core import ElementConstructor, AbstractElement
from idom.server.prefab import AbstractRenderServer
from idom.server.utils import find_available_port
from idom.server.sanic import PerClientStateServer
from idom.testing import (
    create_selenium_page_get_and_display_context,
    open_sanic_mount_and_server,
    open_selenium_chrome_driver,
    create_sanic_server_type_for_testing,
)


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
        "--no-restore",
        dest="restore_client",
        action="store_false",
        help="Whether to restore the client build before testing.",
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
def display(driver_get_and_display_content):
    with driver_get_and_display_content[1]() as display:
        yield display


@pytest.fixture
def driver_get(driver_get_and_display_content):
    return driver_get_and_display_content[0]


@pytest.fixture
def driver_get_and_display_content(
    driver: Chrome,
    server: AbstractRenderServer,
    server_url: str,
    mount: Callable[..., None],
) -> Iterator[Callable[[Union[ElementConstructor, AbstractElement], str], None]]:
    """A function for displaying an element using the current web driver."""
    return create_selenium_page_get_and_display_context(
        driver, server, server_url, mount
    )


@pytest.fixture
def driver_wait(driver: Chrome) -> WebDriverWait:
    """A :class:`WebDriverWait` object for the current web driver"""
    return WebDriverWait(driver, 3)


@pytest.fixture(scope="session")
def display_id() -> idom.Ref[int]:
    return idom.Ref(0)


@pytest.fixture(scope="module")
def driver(create_driver: Callable[[], Chrome]) -> Chrome:
    """A Selenium web driver"""
    return create_driver()


@pytest.fixture(scope="module")
def create_driver(pytestconfig: Config):
    """A Selenium web driver"""
    with ExitStack() as exit_stack:

        def create():
            return exit_stack.enter_context(
                open_selenium_chrome_driver(headless=bool(pytestconfig.option.headless))
            )

        yield create


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
    with open_sanic_mount_and_server(
        fixturized_server_type, host=host, port=port, app=application
    ) as mount_and_server:
        yield mount_and_server


@pytest.fixture(scope="module")
def application():
    return sanic.Sanic()


@pytest.fixture(scope="module")
def last_server_error(fixturized_server_type):
    """A ``Ref`` containing the last server error. This must be populated by ``server_type``"""
    return fixturized_server_type.last_server_error_for_idom_testing


@pytest.fixture(scope="module")
def fixturized_server_type(server_type):
    return create_sanic_server_type_for_testing(server_type)


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


@pytest.fixture
def client_implementation():
    original = idom.client.current
    try:
        yield idom.client
    finally:
        idom.client.current = original


@pytest.fixture(scope="session", autouse=True)
def _restore_client(pytestconfig: Config) -> Iterator[None]:
    """Restore the client's state before and after testing

    For faster test runs set ``--no-restore-client`` at the CLI. Test coverage and
    breakages may occur if this is set. Further the client is not cleaned up
    after testing and may effect usage of IDOM beyond the scope of the tests.
    """
    if pytestconfig.option.restore_client:
        manage_client.restore()
        yield
        manage_client.restore()
    else:
        yield
