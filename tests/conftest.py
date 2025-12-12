from __future__ import annotations

import os

import pytest
from _pytest.config.argparsing import Parser

from reactpy.config import (
    REACTPY_ASYNC_RENDERING,
    REACTPY_DEBUG,
)
from reactpy.testing import (
    BackendFixture,
    DisplayFixture,
    capture_reactpy_logs,
)
from reactpy.testing.common import GITHUB_ACTIONS

REACTPY_ASYNC_RENDERING.set_current(True)
REACTPY_DEBUG.set_current(True)


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--headless",
        dest="headless",
        action="store_true",
        help="Don't open a browser window when running web-based tests",
    )


@pytest.fixture(scope="session")
async def display(server, browser):
    async with DisplayFixture(backend=server, browser=browser) as display:
        yield display


@pytest.fixture(scope="session")
async def server():
    async with BackendFixture() as server:
        yield server


@pytest.fixture(scope="session")
async def browser(pytestconfig: pytest.Config):
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        yield await pw.chromium.launch(headless=_headless_environ(pytestconfig))


@pytest.fixture(autouse=True)
def assert_no_logged_exceptions():
    with capture_reactpy_logs() as records:
        yield
        try:
            for r in records:
                if r.exc_info is not None:
                    raise r.exc_info[1]
        finally:
            records.clear()


def _headless_environ(pytestconfig: pytest.Config):
    if (
        pytestconfig.getoption("headless")
        or os.environ.get("PLAYWRIGHT_HEADLESS") == "1"
        or GITHUB_ACTIONS
    ):
        os.environ["PLAYWRIGHT_HEADLESS"] = "1"
        return True
    return False
