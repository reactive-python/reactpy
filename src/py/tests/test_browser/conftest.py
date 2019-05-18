import time

import pytest

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

import idom


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        help="Whether to run browser tests in headless mode.",
    )


@pytest.fixture(scope="session")
def display(driver):
    _display, element = idom.hotswap()
    server = idom.server.sanic.PerClientState(element)
    server.daemon("localhost", "8765")

    def display(element):
        _display(element)
        driver.get("http://localhost:8765/client/index.html")

    time.sleep(1)  # wait for server start
    return display


@pytest.fixture(scope="session")
def driver(pytestconfig):
    chrome_options = Options()

    if pytestconfig.option.headless:
        chrome_options.headless = True

    driver = Chrome(options=chrome_options)

    driver.set_window_size(1080, 800)
    driver.set_page_load_timeout(5)
    driver.implicitly_wait(5)

    try:
        yield driver
    finally:
        driver.quit()
