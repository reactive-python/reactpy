# ruff: noqa: S701
import asyncio
from pathlib import Path

import pytest
from jinja2 import Environment as JinjaEnvironment
from jinja2 import FileSystemLoader as JinjaFileSystemLoader
from requests import request
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.templating import Jinja2Templates

import reactpy
from reactpy.asgi.middleware import ReactPyMiddleware
from reactpy.config import REACTPY_PATH_PREFIX, REACTPY_TESTS_DEFAULT_TIMEOUT
from reactpy.testing import BackendFixture, DisplayFixture


@pytest.fixture()
async def display(page):
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


def test_invalid_path_prefix():
    with pytest.raises(ValueError, match="Invalid `path_prefix`*"):

        async def app(scope, receive, send):
            pass

        ReactPyMiddleware(app, root_components=["abc"], path_prefix="invalid")


def test_invalid_web_modules_dir():
    with pytest.raises(
        ValueError, match='Web modules directory "invalid" does not exist.'
    ):

        async def app(scope, receive, send):
            pass

        ReactPyMiddleware(app, root_components=["abc"], web_modules_dir=Path("invalid"))


async def test_unregistered_root_component():
    templates = Jinja2Templates(
        env=JinjaEnvironment(
            loader=JinjaFileSystemLoader("tests/templates"),
            extensions=["reactpy.templatetags.Jinja"],
        )
    )

    async def homepage(request):
        return templates.TemplateResponse(request, "index.html")

    @reactpy.component
    def Stub():
        return reactpy.html.p("Hello")

    app = Starlette(routes=[Route("/", homepage)])
    app = ReactPyMiddleware(app, root_components=["tests.sample.SampleApp"])

    async with BackendFixture(app) as server:
        async with DisplayFixture(backend=server) as new_display:
            await new_display.show(Stub)

            # Wait for the log record to be popualted
            for _ in range(10):
                if len(server.log_records) > 0:
                    break
                await asyncio.sleep(0.25)

            # Check that the log record was populated with the "unregistered component" message
            assert (
                "Attempting to use an unregistered root component"
                in server.log_records[-1].message
            )


async def test_display_simple_hello_world(display: DisplayFixture):
    @reactpy.component
    def Hello():
        return reactpy.html.p({"id": "hello"}, ["Hello World"])

    await display.show(Hello)

    await display.page.wait_for_selector("#hello")

    # test that we can reconnect successfully
    await display.page.reload()

    await display.page.wait_for_selector("#hello")


async def test_static_file_not_found(page):
    async def app(scope, receive, send): ...

    app = ReactPyMiddleware(app, [])

    async with BackendFixture(app) as server:
        url = f"http://{server.host}:{server.port}{REACTPY_PATH_PREFIX.current}static/invalid.js"
        response = await asyncio.to_thread(
            request, "GET", url, timeout=REACTPY_TESTS_DEFAULT_TIMEOUT.current
        )
        assert response.status_code == 404
