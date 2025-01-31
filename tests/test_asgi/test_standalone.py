from collections.abc import MutableMapping

import pytest
from requests import request

import reactpy
from reactpy import html
from reactpy.asgi.standalone import ReactPy
from reactpy.testing import BackendFixture, DisplayFixture, poll
from reactpy.testing.common import REACTPY_TESTS_DEFAULT_TIMEOUT
from reactpy.types import Connection, Location


@pytest.fixture()
async def display(page, request):
    async with BackendFixture() as server:
        async with DisplayFixture(backend=server, driver=page) as display:
            yield display


async def test_display_simple_hello_world(display: DisplayFixture):
    @reactpy.component
    def Hello():
        return reactpy.html.p({"id": "hello"}, ["Hello World"])

    await display.show(Hello)

    await display.page.wait_for_selector("#hello")

    # test that we can reconnect successfully
    await display.page.reload()

    await display.page.wait_for_selector("#hello")


async def test_display_simple_click_counter(display: DisplayFixture):
    @reactpy.component
    def Counter():
        count, set_count = reactpy.hooks.use_state(0)
        return reactpy.html.button(
            {
                "id": "counter",
                "on_click": lambda event: set_count(lambda old_count: old_count + 1),
            },
            f"Count: {count}",
        )

    await display.show(Counter)

    counter = await display.page.wait_for_selector("#counter")

    for i in range(5):
        await poll(counter.text_content).until_equals(f"Count: {i}")
        await counter.click()


async def test_use_connection(display: DisplayFixture):
    conn = reactpy.Ref()

    @reactpy.component
    def ShowScope():
        conn.current = reactpy.use_connection()
        return html.pre({"id": "scope"}, str(conn.current))

    await display.show(ShowScope)

    await display.page.wait_for_selector("#scope")
    assert isinstance(conn.current, Connection)


async def test_use_scope(display: DisplayFixture):
    scope = reactpy.Ref()

    @reactpy.component
    def ShowScope():
        scope.current = reactpy.use_scope()
        return html.pre({"id": "scope"}, str(scope.current))

    await display.show(ShowScope)

    await display.page.wait_for_selector("#scope")
    assert isinstance(scope.current, MutableMapping)


async def test_use_location(display: DisplayFixture):
    location = reactpy.Ref()

    @poll
    async def poll_location():
        """This needs to be async to allow the server to respond"""
        return getattr(location, "current", None)

    @reactpy.component
    def ShowRoute():
        location.current = reactpy.use_location()
        return html.pre(str(location.current))

    await display.show(ShowRoute)

    await poll_location.until_equals(Location("/", ""))

    for loc in [
        Location("/something", ""),
        Location("/something/file.txt", ""),
        Location("/another/something", ""),
        Location("/another/something/file.txt", ""),
        Location("/another/something/file.txt", "?key=value"),
        Location("/another/something/file.txt", "?key1=value1&key2=value2"),
    ]:
        await display.goto(loc.path + loc.query_string)
        await poll_location.until_equals(loc)


async def test_carrier(display: DisplayFixture):
    hook_val = reactpy.Ref()

    @reactpy.component
    def ShowRoute():
        hook_val.current = reactpy.hooks.use_connection().carrier
        return html.pre({"id": "hook"}, str(hook_val.current))

    await display.show(ShowRoute)

    await display.page.wait_for_selector("#hook")

    # we can't easily narrow this check
    assert hook_val.current is not None


async def test_customized_head(page):
    custom_title = "Custom Title for ReactPy"

    @reactpy.component
    def sample():
        return html.h1(f"^ Page title is customized to: '{custom_title}'")

    app = ReactPy(sample, html_head=html.head(html.title(custom_title)))

    async with BackendFixture(app) as server:
        async with DisplayFixture(backend=server, driver=page) as new_display:
            await new_display.show(sample)
            assert (await new_display.page.title()) == custom_title


async def test_head_request(page):
    @reactpy.component
    def sample():
        return html.h1("Hello World")

    app = ReactPy(sample)

    async with BackendFixture(app) as server:
        async with DisplayFixture(backend=server, driver=page) as new_display:
            await new_display.show(sample)
            url = f"http://{server.host}:{server.port}"
            response = request(
                "HEAD", url, timeout=REACTPY_TESTS_DEFAULT_TIMEOUT.current
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/html; charset=utf-8"
            assert response.headers["cache-control"] == "max-age=60, public"
            assert response.headers["access-control-allow-origin"] == "*"
            assert response.content == b""
