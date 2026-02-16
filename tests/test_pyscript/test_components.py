from pathlib import Path

import pytest

import reactpy
from reactpy import html, pyscript_component
from reactpy.executors.asgi import ReactPy
from reactpy.testing import BackendFixture, DisplayFixture
from reactpy.testing.backend import root_hotswap_component


@pytest.fixture(scope="module")
async def display(browser):
    """Override for the display fixture that uses ReactPyMiddleware."""
    app = ReactPy(root_hotswap_component, pyscript_setup=True)

    async with BackendFixture(app) as server:
        async with DisplayFixture(backend=server, browser=browser) as new_display:
            yield new_display


async def test_pyscript_component(display: DisplayFixture):
    @reactpy.component
    def Counter():
        return pyscript_component(
            Path(__file__).parent / "pyscript_components" / "root.py",
            initial=html.div({"id": "loading"}, "Loading..."),
        )

    await display.show(Counter)

    await display.page.wait_for_selector("#loading")
    await display.page.wait_for_selector("#incr")

    await display.page.click("#incr")
    await display.page.wait_for_selector("#incr[data-count='1']")

    await display.page.click("#incr")
    await display.page.wait_for_selector("#incr[data-count='2']")

    await display.page.click("#incr")
    await display.page.wait_for_selector("#incr[data-count='3']")


async def test_custom_root_name(display: DisplayFixture):
    @reactpy.component
    def CustomRootName():
        return pyscript_component(
            Path(__file__).parent / "pyscript_components" / "custom_root_name.py",
            initial=html.div({"id": "loading"}, "Loading..."),
            root="custom",
        )

    await display.show(CustomRootName)

    await display.page.wait_for_selector("#loading")
    await display.page.wait_for_selector("#incr")

    await display.page.click("#incr")
    await display.page.wait_for_selector("#incr[data-count='1']")

    await display.page.click("#incr")
    await display.page.wait_for_selector("#incr[data-count='2']")

    await display.page.click("#incr")
    await display.page.wait_for_selector("#incr[data-count='3']")


def test_bad_file_path():
    with pytest.raises(ValueError):
        pyscript_component(initial=html.div({"id": "loading"}, "Loading...")).render()
