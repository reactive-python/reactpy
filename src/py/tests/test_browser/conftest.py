import time

import pytest

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

import idom


def pytest_addoption(parser):
    parser.addoption(
        "--selenium-headless",
        action="store_true",
        help="Whether to run browser tests in headless mode.",
    )


@pytest.fixture(scope="session")
def display(webdriver):
    _display, element = idom.hotswap()
    server = idom.server.sanic.PerClientState(element)
    server.daemon("localhost", "8765")

    def display(element):
        _display(element)
        webdriver.get("http://localhost:8765/client/index.html")

    time.sleep(1)  # wait for server start
    return display


@pytest.fixture
def implicit_wait(webdriver):
    webdriver.implicitly_wait(5)


@pytest.fixture
def wait(webdriver):
    def wait(timeout, condition, *args, **kwargs):
        if isinstance(condition, str):
            condition_check = getattr(expected_conditions, condition)
        else:
            condition_check = condition(*args, **kwargs)
        return WebDriverWait(webdriver, timeout).until(condition_check)

    return wait


@pytest.fixture
def wait_by(wait):
    def wait_by(timeout, condition, locator_type, locator_value):
        locate_by = getattr(By, locator_type.upper())
        return wait(timeout, condition, (locate_by, locator_value))

    return wait_by


@pytest.fixture(scope="session")
def webdriver(pytestconfig):
    chrome_options = Options()

    chrome_options.headless = True

    driver = Chrome(options=chrome_options)

    driver.set_page_load_timeout(5)

    try:
        yield driver
    finally:
        driver.quit()
