import logging
import inspect
from typing import Any, Iterator, Iterable

from loguru import logger
import pytest
from _pytest.logging import caplog as _caplog, LogCaptureFixture  # noqa
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait

import pyalect.builtins.pytest  # noqa

import idom
from idom.client import manage as manage_client
from idom.testing import ServerMountPoint, create_simple_selenium_web_driver


def pytest_collection_modifyitems(items: Iterable[Any]) -> None:
    for item in items:
        if isinstance(item, pytest.Function):
            if inspect.iscoroutinefunction(item.function):
                item.add_marker(pytest.mark.asyncio)


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


@pytest.fixture
def display(driver, server_mount_point, mount):
    display_id = idom.Ref(0)

    def mount_and_display(element_constructor, query=None, check_mount=True):
        element_id = f"display-{display_id.set_current(display_id.current + 1)}"
        mount(lambda: idom.html.div({"id": element_id}, element_constructor()))
        driver.get(server_mount_point.url(query=query))
        if check_mount:
            driver.find_element_by_id(element_id)
        return element_id

    yield mount_and_display


@pytest.fixture
def driver_get(driver, server_mount_point):
    return lambda query=None: driver.get(server_mount_point.url(query=query))


@pytest.fixture
def mount(server_mount_point):
    with server_mount_point.open_mount_function() as mount:
        yield mount


@pytest.fixture
def last_server_error(server_mount_point):
    return server_mount_point.server.last_server_error_for_idom_testing


@pytest.fixture
def server_mount_point():
    """An IDOM layout mount function and server as a tuple

    The ``mount`` and ``server`` fixtures use this.
    """
    mount_point = ServerMountPoint(server_config={"cors": True})
    yield mount_point
    mount_point.server.stop()


@pytest.fixture(scope="module")
def driver_wait(driver):
    return WebDriverWait(driver, 3)


@pytest.fixture(scope="module")
def driver(create_driver) -> Chrome:
    """A Selenium web driver"""
    return create_driver()


@pytest.fixture(scope="module")
def create_driver(driver_is_headless):
    """A Selenium web driver"""
    drivers = []

    def create():
        options = ChromeOptions()
        options.headless = driver_is_headless
        driver = create_simple_selenium_web_driver(driver_options=options)
        drivers.append(driver)
        return driver

    yield create

    for d in drivers:
        d.quit()


@pytest.fixture(scope="session")
def driver_is_headless(pytestconfig: Config):
    return bool(pytestconfig.option.headless)


@pytest.fixture(autouse=True)
def caplog(_caplog: LogCaptureFixture) -> Iterator[LogCaptureFixture]:

    handler_id = logger.add(_PropogateHandler(), format="{message}")
    yield _caplog
    logger.remove(handler_id)
    assert not _caplog.record_tuples


class _PropogateHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)


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
