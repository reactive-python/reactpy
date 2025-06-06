from __future__ import annotations

from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)

from reactpy.config import REACTPY_TESTS_DEFAULT_TIMEOUT
from reactpy.testing.backend import BackendFixture
from reactpy.types import RootComponentConstructor


class DisplayFixture:
    """A fixture for running web-based tests using ``playwright``"""

    _exit_stack: AsyncExitStack

    def __init__(
        self,
        backend: BackendFixture | None = None,
        driver: Browser | BrowserContext | Page | None = None,
    ) -> None:
        if backend is not None:
            self.backend = backend
        if driver is not None:
            if isinstance(driver, Page):
                self.page = driver
            else:
                self._browser = driver

    async def show(
        self,
        component: RootComponentConstructor,
    ) -> None:
        self.backend.mount(component)
        await self.goto("/")

    async def goto(self, path: str, query: Any | None = None) -> None:
        await self.page.goto(self.backend.url(path, query))

    async def __aenter__(self) -> DisplayFixture:
        es = self._exit_stack = AsyncExitStack()

        browser: Browser | BrowserContext
        if not hasattr(self, "page"):
            if not hasattr(self, "_browser"):
                pw = await es.enter_async_context(async_playwright())
                browser = await pw.chromium.launch()
            else:
                browser = self._browser
            self.page = await browser.new_page()

        self.page.set_default_timeout(REACTPY_TESTS_DEFAULT_TIMEOUT.current * 1000)

        if not hasattr(self, "backend"):  # nocov
            self.backend = BackendFixture()
            await es.enter_async_context(self.backend)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.backend.mount(None)
        await self._exit_stack.aclose()
