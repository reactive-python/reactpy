from __future__ import annotations

import os
from contextlib import AsyncExitStack
from types import TracebackType
from typing import TYPE_CHECKING, Any

from playwright.async_api import Browser, Page, async_playwright, expect

from reactpy.config import REACTPY_TESTS_DEFAULT_TIMEOUT as DEFAULT_TIMEOUT
from reactpy.testing.backend import BackendFixture
from reactpy.types import RootComponentConstructor

if TYPE_CHECKING:
    import pytest


class DisplayFixture:
    """A fixture for running web-based tests using ``playwright``"""

    page: Page
    browser_is_external: bool = False
    backend_is_external: bool = False

    def __init__(
        self,
        backend: BackendFixture | None = None,
        browser: Browser | None = None,
        headless: bool = False,
        timeout: float | None = None,
    ) -> None:
        if backend:
            self.backend_is_external = True
            self.backend = backend

        if browser:
            self.browser_is_external = True
            self.browser = browser

        self.timeout = DEFAULT_TIMEOUT.current if timeout is None else timeout
        self.headless = headless

    async def show(
        self,
        component: RootComponentConstructor,
    ) -> None:
        self.backend.mount(component)
        await self.goto("/")

    async def goto(self, path: str, query: Any | None = None) -> None:
        await self.configure_page()
        await self.page.goto(self.backend.url(path, query))

    async def __aenter__(self) -> DisplayFixture:
        self.exit_stack = AsyncExitStack()

        if not hasattr(self, "browser"):
            pw = await self.exit_stack.enter_async_context(async_playwright())
            self.browser = await self.exit_stack.enter_async_context(
                await pw.chromium.launch(headless=not _playwright_visible())
            )

        expect.set_options(timeout=self.timeout * 1000)
        await self.configure_page()

        if not hasattr(self, "backend"):  # nocov
            self.backend = BackendFixture()
            await self.exit_stack.enter_async_context(self.backend)

        return self

    async def configure_page(self) -> None:
        if getattr(self, "page", None) is None:
            self.page = await self.browser.new_page()
            self.page = await self.exit_stack.enter_async_context(self.page)
            self.page.set_default_navigation_timeout(self.timeout * 1000)
            self.page.set_default_timeout(self.timeout * 1000)
            self.page.on("console", lambda x: print(f"BROWSER CONSOLE: {x.text}"))  # noqa: T201
            self.page.on(
                "pageerror",
                lambda x: print(f"BROWSER ERROR: {x.name} - {x.message}\n{x.stack}"),  # noqa: T201
            )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.backend.mount(None)
        await self.exit_stack.aclose()


def _playwright_visible(pytestconfig: pytest.Config | None = None) -> bool:
    if (pytestconfig and pytestconfig.getoption("visible")) or os.environ.get(
        "PLAYWRIGHT_VISIBLE"
    ) == "1":
        os.environ.setdefault("PLAYWRIGHT_VISIBLE", "1")
        return True
    return False
