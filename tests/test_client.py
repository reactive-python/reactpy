import asyncio
from contextlib import AsyncExitStack
from pathlib import Path

from playwright.async_api import Page

import reactpy
from reactpy.testing import BackendFixture, DisplayFixture, poll
from reactpy.testing.utils import find_available_port
from tests.tooling.common import DEFAULT_TYPE_DELAY
from tests.tooling.hooks import use_counter

JS_DIR = Path(__file__).parent / "js"


async def test_automatic_reconnect(
    display: DisplayFixture, page: Page, server: BackendFixture
):
    @reactpy.component
    def SomeComponent():
        count, incr_count = use_counter(0)
        return reactpy.html.fragment(
            reactpy.html.p({"data_count": count, "id": "count"}, "count", count),
            reactpy.html.button(
                {"on_click": lambda e: incr_count(), "id": "incr"}, "incr"
            ),
        )

    async def get_count():
        # need to refetch element because may unmount on reconnect
        count = await page.wait_for_selector("#count")
        return await count.get_attribute("data-count")

    await display.show(SomeComponent)

    await poll(get_count).until_equals("0")
    incr = await page.wait_for_selector("#incr")
    await incr.click()

    await poll(get_count).until_equals("1")
    incr = await page.wait_for_selector("#incr")
    await incr.click()

    await poll(get_count).until_equals("2")
    incr = await page.wait_for_selector("#incr")
    await incr.click()

    await server.restart()
    await display.show(SomeComponent)

    await poll(get_count).until_equals("0")
    incr = await page.wait_for_selector("#incr")
    await incr.click()

    await poll(get_count).until_equals("1")
    incr = await page.wait_for_selector("#incr")
    await incr.click()

    await poll(get_count).until_equals("2")
    incr = await page.wait_for_selector("#incr")
    await incr.click()


async def test_style_can_be_changed(display: DisplayFixture):
    """This test was introduced to verify the client does not mutate the model

    A bug was introduced where the client-side model was mutated and React was relying
    on the model to have been copied in order to determine if something had changed.

    See for more info: https://github.com/reactive-python/reactpy/issues/480
    """

    @reactpy.component
    def ButtonWithChangingColor():
        color_toggle, set_color_toggle = reactpy.hooks.use_state(True)
        color = "red" if color_toggle else "blue"
        return reactpy.html.button(
            {
                "id": "my-button",
                "on_click": lambda event: set_color_toggle(not color_toggle),
                "style": {"background_color": color, "color": "white"},
            },
            f"color: {color}",
        )

    await display.show(ButtonWithChangingColor)

    button = await display.page.wait_for_selector("#my-button")

    await poll(_get_style, button).until(
        lambda style: style["background-color"] == "red"
    )

    for color in ["blue", "red"] * 2:
        await button.click()
        await poll(_get_style, button).until(
            lambda style, c=color: style["background-color"] == c
        )


async def _get_style(element):
    items = (await element.get_attribute("style")).split(";")
    pairs = [item.split(":", 1) for item in map(str.strip, items) if item]
    return {key.strip(): value.strip() for key, value in pairs}


async def test_slow_server_response_on_input_change(display: DisplayFixture):
    """A delay server-side could cause input values to be overwritten.

    For more info see: https://github.com/reactive-python/reactpy/issues/684
    """

    delay = 0.2

    @reactpy.component
    def SomeComponent():
        value, set_value = reactpy.hooks.use_state("")

        async def handle_change(event):
            await asyncio.sleep(delay)
            set_value(event["target"]["value"])

        return reactpy.html.input({"on_change": handle_change, "id": "test-input"})

    await display.show(SomeComponent)

    inp = await display.page.wait_for_selector("#test-input")
    await inp.type("hello", delay=DEFAULT_TYPE_DELAY)

    assert (await inp.evaluate("node => node.value")) == "hello"


async def test_snake_case_attributes(display: DisplayFixture):
    @reactpy.component
    def SomeComponent():
        return reactpy.html.h1(
            {
                "id": "my-title",
                "style": {"background_color": "blue"},
                "class_name": "hello",
                "data_some_thing": "some-data",
                "aria_some_thing": "some-aria",
            },
            "title with some attributes",
        )

    await display.show(SomeComponent)

    title = await display.page.wait_for_selector("#my-title")

    assert await title.get_attribute("class") == "hello"
    assert await title.get_attribute("style") == "background-color: blue;"
    assert await title.get_attribute("data-some-thing") == "some-data"
    assert await title.get_attribute("aria-some-thing") == "some-aria"
