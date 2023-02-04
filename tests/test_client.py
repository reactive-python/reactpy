import asyncio
from contextlib import AsyncExitStack
from pathlib import Path

from playwright.async_api import Browser

import idom
from idom.backend.utils import find_available_port
from idom.testing import BackendFixture, DisplayFixture, poll
from tests.tooling.common import DEFAULT_TYPE_DELAY
from tests.tooling.hooks import use_counter


JS_DIR = Path(__file__).parent / "js"


async def test_automatic_reconnect(browser: Browser):
    port = find_available_port("localhost")
    page = await browser.new_page()

    # we need to wait longer here because the automatic reconnect is not instant
    page.set_default_timeout(10000)

    @idom.component
    def SomeComponent():
        count, incr_count = use_counter(0)
        return idom.html._(
            idom.html.p("count", count, data_count=count, id="count"),
            idom.html.button("incr", on_click=lambda e: incr_count(), id="incr"),
        )

    async with AsyncExitStack() as exit_stack:
        server = await exit_stack.enter_async_context(BackendFixture(port=port))
        display = await exit_stack.enter_async_context(
            DisplayFixture(server, driver=page)
        )

        await display.show(SomeComponent)

        count = await page.wait_for_selector("#count")
        incr = await page.wait_for_selector("#incr")

        for i in range(3):
            assert (await count.get_attribute("data-count")) == str(i)
            await incr.click()

    # the server is disconnected but the last view state is still shown
    await page.wait_for_selector("#count")

    async with AsyncExitStack() as exit_stack:
        server = await exit_stack.enter_async_context(BackendFixture(port=port))
        display = await exit_stack.enter_async_context(
            DisplayFixture(server, driver=page)
        )

        # use mount instead of show to avoid a page refesh
        display.backend.mount(SomeComponent)

        async def get_count():
            # need to refetch element because may unmount on reconnect
            count = await page.wait_for_selector("#count")
            return await count.get_attribute("data-count")

        for i in range(3):
            # it may take a moment for the websocket to reconnect so need to poll
            await poll(get_count).until_equals(str(i))

            # need to refetch element because may unmount on reconnect
            incr = await page.wait_for_selector("#incr")

            await incr.click()


async def test_style_can_be_changed(display: DisplayFixture):
    """This test was introduced to verify the client does not mutate the model

    A bug was introduced where the client-side model was mutated and React was relying
    on the model to have been copied in order to determine if something had changed.

    See for more info: https://github.com/idom-team/idom/issues/480
    """

    @idom.component
    def ButtonWithChangingColor():
        color_toggle, set_color_toggle = idom.hooks.use_state(True)
        color = "red" if color_toggle else "blue"
        return idom.html.button(
            f"color: {color}",
            id="my-button",
            on_click=lambda event: set_color_toggle(not color_toggle),
            style={"background_color": color, "color": "white"},
        )

    await display.show(ButtonWithChangingColor)

    button = await display.page.wait_for_selector("#my-button")

    assert (await _get_style(button))["background-color"] == "red"

    for color in ["blue", "red"] * 2:
        await button.click()
        assert (await _get_style(button))["background-color"] == color


async def _get_style(element):
    items = (await element.get_attribute("style")).split(";")
    pairs = [item.split(":", 1) for item in map(str.strip, items) if item]
    return {key.strip(): value.strip() for key, value in pairs}


async def test_slow_server_response_on_input_change(display: DisplayFixture):
    """A delay server-side could cause input values to be overwritten.

    For more info see: https://github.com/idom-team/idom/issues/684
    """

    delay = 0.2

    @idom.component
    def SomeComponent():
        value, set_value = idom.hooks.use_state("")

        async def handle_change(event):
            await asyncio.sleep(delay)
            set_value(event["target"]["value"])

        return idom.html.input(on_change=handle_change, id="test-input")

    await display.show(SomeComponent)

    inp = await display.page.wait_for_selector("#test-input")
    await inp.type("hello", delay=DEFAULT_TYPE_DELAY)

    assert (await inp.evaluate("node => node.value")) == "hello"


async def test_data_and_aria_attribute_naming(display: DisplayFixture):
    @idom.component
    def SomeComponent():
        return idom.html.h1(
            "see attributes",
            id="title",
            data_some_thing="some data",
            aria_description="some title",
            **{"data-another-thing": "more data"},
        )

    await display.show(SomeComponent)

    title = await display.page.wait_for_selector("#title")

    assert await title.get_attribute("data-some-thing") == "some data"
    assert await title.get_attribute("data-another-thing") == "more data"
    assert await title.get_attribute("aria-description") == "some title"
