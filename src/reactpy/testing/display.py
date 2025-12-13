from __future__ import annotations

import os
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any

from playwright.async_api import Browser, Page, async_playwright, expect

from reactpy.config import REACTPY_TESTS_DEFAULT_TIMEOUT
from reactpy.testing.backend import BackendFixture
from reactpy.testing.common import GITHUB_ACTIONS
from reactpy.types import RootComponentConstructor


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

        self.timeout = (
            timeout if timeout is not None else REACTPY_TESTS_DEFAULT_TIMEOUT.current
        )
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
        self.browser_exit_stack = AsyncExitStack()
        self.backend_exit_stack = AsyncExitStack()

        if not hasattr(self, "browser"):
            pw = await self.browser_exit_stack.enter_async_context(async_playwright())
            self.browser = await pw.chromium.launch(
                headless=self.headless
                or os.environ.get("PLAYWRIGHT_HEADLESS") == "1"
                or GITHUB_ACTIONS
            )

        expect.set_options(timeout=self.timeout * 1000)
        await self.configure_page()

        if not hasattr(self, "backend"):  # nocov
            self.backend = BackendFixture()
            await self.backend_exit_stack.enter_async_context(self.backend)

        return self

    async def configure_page(self) -> None:
        if getattr(self, "page", None) is None:
            self.page = await self.browser.new_page()
            self.page.set_default_navigation_timeout(self.timeout * 1000)
            self.page.set_default_timeout(self.timeout * 1000)
            self.page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))  # noqa: T201
            self.page.on("pageerror", lambda exc: print(f"BROWSER ERROR: {exc}"))  # noqa: T201

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.backend.mount(None)
        if getattr(self, "page", None) is not None:
            await self.page.close()
        if not self.browser_is_external:
            await self.browser_exit_stack.aclose()
        if not self.backend_is_external:
            await self.backend_exit_stack.aclose()
