# ruff: noqa: S701
from pathlib import Path

import pytest
from jinja2 import Environment as JinjaEnvironment
from jinja2 import FileSystemLoader as JinjaFileSystemLoader
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.templating import Jinja2Templates

import reactpy
from reactpy.asgi.middleware import ReactPyMiddleware
from reactpy.testing import BackendFixture, DisplayFixture


@pytest.fixture()
async def display(page):
    templates = Jinja2Templates(
        env=JinjaEnvironment(
            loader=JinjaFileSystemLoader("tests/templates"),
            extensions=["reactpy.jinja.ReactPyTemplateTag"],
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

        reactpy.ReactPyMiddleware(app, root_components=["abc"], path_prefix="invalid")


def test_invalid_web_modules_dir():
    with pytest.raises(
        ValueError, match='Web modules directory "invalid" does not exist.'
    ):

        async def app(scope, receive, send):
            pass

        reactpy.ReactPyMiddleware(
            app, root_components=["abc"], web_modules_dir=Path("invalid")
        )


async def test_unregistered_root_component():
    templates = Jinja2Templates(
        env=JinjaEnvironment(
            loader=JinjaFileSystemLoader("tests/templates"),
            extensions=["reactpy.jinja.ReactPyTemplateTag"],
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
