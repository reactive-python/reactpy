import time

import pytest

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

import idom
from idom.server.sanic import PerClientState


# Default is an error because we want to know whether we are setting the last
# error while testing. A refactor could miss the code path that catches serve
# errors.
default_error = NotImplementedError()
last_server_error = idom.Var(default_error)


class ServerWithErrorCatch(PerClientState):
    async def _stream_route(self, request, socket):
        last_server_error.set(None)
        try:
            await super()._stream_route(request, socket)
        except Exception as e:
            last_server_error.set(e)


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        help="Whether to run browser tests in headless mode.",
    )


@pytest.fixture
def display(_display):
    try:
        yield _display
    finally:
        last_error = last_server_error.get()
        if last_error is default_error:
            raise NotImplementedError(
                "Unable to check for server errors while testing."
            )
        elif last_error is not None:
            raise last_error


@pytest.fixture(scope="session")
def _display(driver):
    _display, element = idom.hotswap()
    server = ServerWithErrorCatch(element)
    server.daemon("localhost", "5678", debug=True)

    def display(element):
        _display(element)
        driver.get("http://localhost:5678/client/index.html")

    time.sleep(1)  # wait for server start
    return display


@pytest.fixture(scope="session")
def driver(pytestconfig):
    chrome_options = Options()

    if pytestconfig.option.headless:
        chrome_options.headless = True

    driver = Chrome(options=chrome_options)

    driver.set_window_size(1080, 800)
    driver.set_page_load_timeout(3)
    driver.implicitly_wait(3)

    try:
        yield driver
    finally:
        driver.quit()
