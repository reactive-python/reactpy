from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Awaitable, Callable, List

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser

import idom
from idom.testing import ServerMountPoint, clear_idom_web_modules_dir
from tests.utils.browser import launch_browser, open_display


def pytest_collection_modifyitems(
    session: pytest.Session, config: Config, items: List[pytest.Item]
) -> None:
    _skip_web_driver_tests_on_windows(items)


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--headless",
        dest="headless",
        action="store_true",
        help="Whether to run browser tests in headless mode.",
    )


@pytest.fixture
async def display(browser):
    async with open_display(browser, idom.server.any) as display:
        yield display


@pytest.fixture
async def browser(pytestconfig: Config):
    async with launch_browser(headless=bool(pytestconfig.option.headless)) as browser:
        yield browser


@pytest.fixture(autouse=True)
def _clear_web_modules_dir_after_test():
    clear_idom_web_modules_dir()


def _skip_web_driver_tests_on_windows(items: List[pytest.Item]) -> None:
    if os.name == "nt":
        for item in items:
            if isinstance(item, pytest.Function):
                if {"display", "driver", "create_driver"}.intersection(
                    item.fixturenames
                ):
                    item.add_marker(
                        pytest.mark.skip(
                            reason="WebDriver tests are not working on Windows",
                        )
                    )
