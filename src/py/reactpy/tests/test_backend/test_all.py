from collections.abc import MutableMapping

import pytest

import reactpy
from reactpy import html
from reactpy.backend import default as default_implementation
from reactpy.backend._common import PATH_PREFIX
from reactpy.backend.types import BackendImplementation, Connection, Location
from reactpy.backend.utils import all_implementations
from reactpy.testing import BackendFixture, DisplayFixture, poll


@pytest.fixture(
    params=[*list(all_implementations()), default_implementation],
    ids=lambda imp: imp.__name__,
    scope="module",
)
async def display(page, request):
    imp: BackendImplementation = request.param

    # we do this to check that route priorities for each backend are correct
    if imp is default_implementation:
        url_prefix = ""
        opts = None
    else:
        url_prefix = str(PATH_PREFIX)
        opts = imp.Options(url_prefix=url_prefix)

    async with BackendFixture(implementation=imp, options=opts) as server:
        async with DisplayFixture(
            backend=server,
            driver=page,
            url_prefix=url_prefix,
        ) as display:
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


async def test_module_from_template(display: DisplayFixture):
    victory = reactpy.web.module_from_template("react", "victory-bar@35.4.0")
    VictoryBar = reactpy.web.export(victory, "VictoryBar")
    await display.show(VictoryBar)
    await display.page.wait_for_selector(".VictoryContainer")


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
        return location.current

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
        await display.goto(loc.pathname + loc.search)
        await poll_location.until_equals(loc)


@pytest.mark.parametrize("hook_name", ["use_request", "use_websocket"])
async def test_use_request(display: DisplayFixture, hook_name):
    hook = getattr(display.backend.implementation, hook_name, None)
    if hook is None:
        pytest.skip(f"{display.backend.implementation} has no '{hook_name}' hook")

    hook_val = reactpy.Ref()

    @reactpy.component
    def ShowRoute():
        hook_val.current = hook()
        return html.pre({"id": "hook"}, str(hook_val.current))

    await display.show(ShowRoute)

    await display.page.wait_for_selector("#hook")

    # we can't easily narrow this check
    assert hook_val.current is not None


@pytest.mark.parametrize("imp", all_implementations())
async def test_customized_head(imp: BackendImplementation, page):
    custom_title = f"Custom Title for {imp.__name__}"

    @reactpy.component
    def sample():
        return html.h1(f"^ Page title is customized to: '{custom_title}'")

    async with BackendFixture(
        implementation=imp,
        options=imp.Options(head=html.title(custom_title)),
    ) as server:
        async with DisplayFixture(backend=server, driver=page) as display:
            await display.show(sample)
            assert (await display.page.title()) == custom_title
