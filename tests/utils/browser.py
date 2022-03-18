from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from playwright.async_api import Browser, Page, async_playwright

from idom import html
from idom.server import any as any_server
from idom.server.types import ServerImplementation
from idom.testing import ServerMountPoint
from idom.types import RootComponentConstructor


@asynccontextmanager
async def launch_browser(headless: bool) -> Browser:
    async with async_playwright() as p:
        yield await p.chromium.launch(headless=headless)


@asynccontextmanager
async def open_display(
    browser: Browser, implementation: ServerImplementation[Any] = any_server
) -> Display:
    async with ServerMountPoint(implementation) as mount:
        page = await browser.new_page()
        try:
            yield Display(page, mount)
        finally:
            await page.close()


class Display:
    def __init__(self, page: Page, mount: ServerMountPoint) -> None:
        self.page = page
        self.mount = mount
        self._next_id = 0

    async def show(
        self, component: RootComponentConstructor, query: dict[str, Any] | None = None
    ) -> str:
        self._next_id += 1
        component_id = f"display-{self._next_id}"
        self.mount.mount(lambda: html.div({"id": component_id}, component()))
        await self.page.goto(self.mount.url(query=query))
        await self.page.wait_for_selector(f"#{component_id}")
        return component_id
