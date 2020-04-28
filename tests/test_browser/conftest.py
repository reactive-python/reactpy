import time

import pytest

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

import idom
from idom.server import hotswap_server
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


@pytest.fixture(scope="package", autouse=True)
def fresh_client():
    idom.client.restore()
    yield
    idom.client.restore()


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
    host, port = "127.0.0.1", 5000
    mount, server = hotswap_server(
        ServerWithErrorCatch, host, port, run_options={"debug": True}
    )

    def display(element):
        mount(element)
        driver.get(f"http://{host}:{port}/client/index.html")

    time.sleep(1)  # wait for server start
    yield display


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
