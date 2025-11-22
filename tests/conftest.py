from __future__ import annotations

import asyncio
import os
import subprocess

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser

from reactpy.config import (
    REACTPY_ASYNC_RENDERING,
    REACTPY_DEBUG,
    REACTPY_TESTS_DEFAULT_TIMEOUT,
)
from reactpy.testing import (
    BackendFixture,
    DisplayFixture,
    capture_reactpy_logs,
    clear_reactpy_web_modules_dir,
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


@pytest.fixture(autouse=True, scope="session")
def install_playwright():
    subprocess.run(["playwright", "install", "chromium"], check=True)  # noqa: S607, S603
    subprocess.run(["playwright", "install-deps"], check=True)  # noqa: S607, S603


@pytest.fixture(autouse=True, scope="session")
def rebuild():
    subprocess.run(["hatch", "build", "-t", "wheel"], check=True)  # noqa: S607, S603


@pytest.fixture(autouse=True, scope="function")
def create_hook_state():
    """This fixture is a bug fix related to `pytest_asyncio`.

    Usually the hook stack is created automatically within the display fixture, but context
    variables aren't retained within `pytest_asyncio` async fixtures. As a workaround,
    this fixture ensures that the hook stack is created before each test is run.

    Ref: https://github.com/pytest-dev/pytest-asyncio/issues/127
    """
    from reactpy.core._life_cycle_hook import HOOK_STACK

    token = HOOK_STACK.initialize()
    yield token
    HOOK_STACK.reset(token)


@pytest.fixture
async def display(server, page):
    async with DisplayFixture(server, page) as display:
        yield display


@pytest.fixture
async def server():
    async with BackendFixture() as server:
        yield server


@pytest.fixture
async def page(browser):
    pg = await browser.new_page()
    pg.set_default_timeout(REACTPY_TESTS_DEFAULT_TIMEOUT.current * 1000)
    try:
        yield pg
    finally:
        await pg.close()


@pytest.fixture
async def browser(pytestconfig: Config):
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        yield await pw.chromium.launch(
            headless=bool(pytestconfig.option.headless) or GITHUB_ACTIONS
        )


@pytest.fixture(scope="session")
def event_loop_policy():
    if os.name == "nt":  # nocov
        return asyncio.WindowsProactorEventLoopPolicy()
    else:
        return asyncio.DefaultEventLoopPolicy()


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
