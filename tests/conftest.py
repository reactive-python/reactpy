from __future__ import annotations

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from playwright.async_api import async_playwright

from idom.server.utils import all_implementations
from idom.testing import DisplayFixture, ServerFixture, clear_idom_web_modules_dir
from tests.tooling.loop import open_event_loop


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--open-browser",
        dest="open_browser",
        action="store_true",
        help="Open a browser window when runnging web-based tests",
    )


@pytest.fixture
async def display(server, browser):
    async with DisplayFixture(server, browser) as display:
        yield display


@pytest.fixture(scope="session", params=list(all_implementations()))
async def server(request):
    async with ServerFixture(implementation=request.param) as server:
        yield server


@pytest.fixture(scope="session")
async def browser(pytestconfig: Config):
    async with async_playwright() as pw:
        yield await pw.chromium.launch(
            headless=not bool(pytestconfig.option.open_browser)
        )


@pytest.fixture(scope="session")
def event_loop():
    with open_event_loop() as loop:
        yield loop


@pytest.fixture(autouse=True)
def clear_web_modules_dir_after_test():
    clear_idom_web_modules_dir()
