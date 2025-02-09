# ruff: noqa: S701
from pathlib import Path

import pytest
from jinja2 import Environment as JinjaEnvironment
from jinja2 import FileSystemLoader as JinjaFileSystemLoader
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from reactpy import html
from reactpy.executors.asgi.pyscript import ReactPyPyscript
from reactpy.testing import BackendFixture, DisplayFixture


@pytest.fixture()
async def display(page):
    """Override for the display fixture that uses ReactPyMiddleware."""
    app = ReactPyPyscript(
        Path(__file__).parent / "pyscript_components" / "root.py",
        initial=html.div({"id": "loading"}, "Loading..."),
    )

    async with BackendFixture(app) as server:
        async with DisplayFixture(backend=server, driver=page) as new_display:
            yield new_display


@pytest.fixture()
async def multi_file_display(page):
    """Override for the display fixture that uses ReactPyMiddleware."""
    app = ReactPyPyscript(
        Path(__file__).parent / "pyscript_components" / "load_first.py",
        Path(__file__).parent / "pyscript_components" / "load_second.py",
        initial=html.div({"id": "loading"}, "Loading..."),
    )

    async with BackendFixture(app) as server:
        async with DisplayFixture(backend=server, driver=page) as new_display:
            yield new_display


@pytest.fixture()
async def jinja_display(page):
    """Override for the display fixture that uses ReactPyMiddleware."""
    templates = Jinja2Templates(
        env=JinjaEnvironment(
            loader=JinjaFileSystemLoader("tests/templates"),
            extensions=["reactpy.templatetags.Jinja"],
        )
    )

    async def homepage(request):
        return templates.TemplateResponse(request, "index.html")

    app = Starlette(routes=[Route("/", homepage)])

    async with BackendFixture(app) as server:
        async with DisplayFixture(backend=server, driver=page) as new_display:
            yield new_display


async def test_root_component(display: DisplayFixture):
    await display.goto("/")

    await display.page.wait_for_selector("#loading")
    await display.page.wait_for_selector("#incr")

    await display.page.click("#incr")
    await display.page.wait_for_selector("#incr[data-count='1']")

    await display.page.click("#incr")
    await display.page.wait_for_selector("#incr[data-count='2']")

    await display.page.click("#incr")
    await display.page.wait_for_selector("#incr[data-count='3']")


async def test_multi_file_components(multi_file_display: DisplayFixture):
    await multi_file_display.goto("/")

    await multi_file_display.page.wait_for_selector("#incr")

    await multi_file_display.page.click("#incr")
    await multi_file_display.page.wait_for_selector("#incr[data-count='1']")

    await multi_file_display.page.click("#incr")
    await multi_file_display.page.wait_for_selector("#incr[data-count='2']")

    await multi_file_display.page.click("#incr")
    await multi_file_display.page.wait_for_selector("#incr[data-count='3']")


def test_bad_file_path():
    with pytest.raises(ValueError):
        ReactPyPyscript()
