from __future__ import annotations

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from playwright.async_api import async_playwright

from idom.testing import DisplayFixture, ServerFixture, clear_idom_web_modules_dir
from tests.tooling.loop import open_event_loop


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--headed",
        dest="headed",
        action="store_true",
        help="Open a browser window when runnging web-based tests",
    )


@pytest.fixture
async def display(server, page):
    async with DisplayFixture(server, page) as display:
        yield display


@pytest.fixture(scope="session")
async def server():
    async with ServerFixture() as server:
        yield server


@pytest.fixture(scope="session")
async def page(browser):
    pg = await browser.new_page()
    pg.set_default_timeout(5000)
    try:
        yield pg
    finally:
        await pg.close()


@pytest.fixture(scope="session")
async def browser(pytestconfig: Config):
    async with async_playwright() as pw:
        yield await pw.chromium.launch(headless=not bool(pytestconfig.option.headed))


@pytest.fixture(scope="session")
def event_loop():
    with open_event_loop() as loop:
        yield loop


@pytest.fixture(autouse=True)
def clear_web_modules_dir_after_test():
    clear_idom_web_modules_dir()
