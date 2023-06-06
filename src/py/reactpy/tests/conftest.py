from __future__ import annotations

import asyncio
import os

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from playwright.async_api import async_playwright

from reactpy.config import REACTPY_TESTING_DEFAULT_TIMEOUT
from reactpy.testing import (
    BackendFixture,
    DisplayFixture,
    capture_reactpy_logs,
    clear_reactpy_web_modules_dir,
)
from tests.tooling.loop import open_event_loop


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--headed",
        dest="headed",
        action="store_true",
        help="Open a browser window when running web-based tests",
    )


@pytest.fixture
async def display(server, page):
    async with DisplayFixture(server, page) as display:
        yield display


@pytest.fixture(scope="session")
async def server():
    async with BackendFixture() as server:
        yield server


@pytest.fixture(scope="session")
async def page(browser):
    pg = await browser.new_page()
    pg.set_default_timeout(REACTPY_TESTING_DEFAULT_TIMEOUT.current * 1000)
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
    if os.name == "nt":  # nocov
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    with open_event_loop() as loop:
        yield loop


@pytest.fixture(autouse=True)
def clear_web_modules_dir_after_test():
    clear_reactpy_web_modules_dir()


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
