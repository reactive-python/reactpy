import logging
import inspect
import time
from socket import socket

from loguru import logger
import pytest
from _pytest.logging import caplog as _caplog  # noqa
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

import pyalect.builtins.pytest  # noqa

import idom
from idom.server import hotswap_server
from idom.server.sanic import PerClientState


# Default is an error because we want to know whether we are setting the last
# error while testing. A refactor could miss the code path that catches serve
# errors.
default_error = NotImplementedError()


def pytest_collection_modifyitems(items):
    for item in items:
        if isinstance(item, pytest.Function):
            if inspect.iscoroutinefunction(item.function):
                item.add_marker(pytest.mark.asyncio)
        if "driver" in item.fixturenames:
            item.add_marker("slow")


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        help="Whether to run browser tests in headless mode.",
    )


@pytest.fixture
def caplog(_caplog):
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    handler_id = logger.add(PropogateHandler(), format="{message}")
    yield _caplog
    logger.remove(handler_id)


@pytest.fixture(scope="session", autouse=True)
def fresh_client():
    idom.client.restore()
    yield
    idom.client.restore()


@pytest.fixture
def display(driver_get, server, mount, host, port, last_server_error):
    def display(element, query=""):
        mount(element)
        driver_get(query)

    try:
        yield display
    finally:
        last_error = last_server_error.get()
        if last_error is default_error:
            msg = f"The server {server} never ran or did not set the 'last_server_error' fixture."
            raise NotImplementedError(msg)
        elif last_error is not None:
            raise last_error


@pytest.fixture
def driver_get(driver, host, port):
    def get(query=""):
        driver.get(f"http://{host}:{port}/client/index.html?{query}")

    return get


@pytest.fixture(scope="session")
def driver(pytestconfig):
    chrome_options = Options()

    if getattr(pytestconfig.option, "headless", False):
        chrome_options.headless = True

    driver = Chrome(options=chrome_options)

    driver.set_window_size(1080, 800)
    driver.set_page_load_timeout(3)
    driver.implicitly_wait(3)

    try:
        yield driver
    finally:
        driver.quit()


@pytest.fixture(scope="module")
def mount(mount_and_server):
    return mount_and_server[0]


@pytest.fixture(scope="module")
def server(mount_and_server):
    server = mount_and_server[1]
    time.sleep(1)
    yield server
    server.stop()


@pytest.fixture(scope="module")
def mount_and_server(server_type, host, port):
    return hotswap_server(server_type, host, port, run_options={"debug": True})


@pytest.fixture(scope="module")
def server_type(last_server_error):
    class ServerWithErrorCatch(PerClientState):
        async def _stream_route(self, request, socket):
            last_server_error.set(None)
            try:
                await super()._stream_route(request, socket)
            except Exception as e:
                last_server_error.set(e)

    return ServerWithErrorCatch


@pytest.fixture(scope="session")
def host():
    return "127.0.0.1"


@pytest.fixture(scope="module")
def port(host):
    sock = socket()
    sock.bind((host, 0))
    return sock.getsockname()[1]


@pytest.fixture(scope="session")
def last_server_error():
    return idom.Var(default_error)


@pytest.fixture(autouse=True)
def _clean_last_server_error(last_server_error):
    last_server_error.set(default_error)
    yield
