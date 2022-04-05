from typing import MutableMapping

import pytest

import idom
from idom import html
from idom.server import default as default_implementation
from idom.server.types import Location
from idom.server.utils import all_implementations
from idom.testing import DisplayFixture, ServerFixture, poll


@pytest.fixture(
    params=list(all_implementations()) + [default_implementation],
    ids=lambda imp: imp.__name__,
    scope="module",
)
async def display(page, request):
    async with ServerFixture(implementation=request.param) as server:
        async with DisplayFixture(server=server, driver=page) as display:
            yield display


async def test_display_simple_hello_world(display: DisplayFixture):
    @idom.component
    def Hello():
        return idom.html.p({"id": "hello"}, ["Hello World"])

    await display.show(Hello)

    await display.page.wait_for_selector("#hello")

    # test that we can reconnect succefully
    await display.page.reload()

    await display.page.wait_for_selector("#hello")


async def test_display_simple_click_counter(display: DisplayFixture):
    @idom.component
    def Counter():
        count, set_count = idom.hooks.use_state(0)
        return idom.html.button(
            {
                "id": "counter",
                "onClick": lambda event: set_count(lambda old_count: old_count + 1),
            },
            f"Count: {count}",
        )

    await display.show(Counter)

    counter = await display.page.wait_for_selector("#counter")

    for i in range(5):
        await poll(counter.text_content).until_equals(f"Count: {i}")
        await counter.click()


async def test_module_from_template(display: DisplayFixture):
    victory = idom.web.module_from_template("react", "victory-bar@35.4.0")
    VictoryBar = idom.web.export(victory, "VictoryBar")
    await display.show(VictoryBar)
    await display.page.wait_for_selector(".VictoryContainer")


async def test_use_scope(display: DisplayFixture):
    scope = idom.Ref()

    @idom.component
    def ShowScope():
        scope.current = display.server.implementation.use_scope()
        return html.pre({"id": "scope"}, str(scope.current))

    await display.show(ShowScope)

    await display.page.wait_for_selector("#scope")
    assert isinstance(scope.current, MutableMapping)


async def test_use_location(display: DisplayFixture):
    location = idom.Ref()

    @poll
    async def poll_location():
        """This needs to be async to allow the server to respond"""
        return location.current

    @idom.component
    def ShowRoute():
        location.current = display.server.implementation.use_location()
        return html.pre({"id": "scope"}, str(location.current))

    await display.show(ShowRoute)

    await poll_location.until_equals(Location("/", ""))

    for loc in [
        Location("/something"),
        Location("/something/file.txt"),
        Location("/another/something"),
        Location("/another/something/file.txt"),
        Location("/another/something/file.txt", "?key=value"),
        Location("/another/something/file.txt", "?key1=value1&key2=value2"),
    ]:
        await display.goto(loc.pathname + loc.search)
        await poll_location.until_equals(loc)
