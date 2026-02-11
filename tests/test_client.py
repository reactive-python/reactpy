import asyncio
from pathlib import Path

import reactpy
from reactpy.testing import BackendFixture, DisplayFixture, poll
from tests.tooling.common import DEFAULT_TYPE_DELAY
from tests.tooling.hooks import use_counter

from . import pytestmark  # noqa: F401

JS_DIR = Path(__file__).parent / "js"


async def test_automatic_reconnect(display: DisplayFixture, server: BackendFixture):
    @reactpy.component
    def SomeComponent():
        count, incr_count = use_counter(0)
        return reactpy.html(
            reactpy.html.p({"data-count": count, "id": "count"}, "count", count),
            reactpy.html.button(
                {"onClick": lambda e: incr_count(), "id": "incr"}, "incr"
            ),
        )

    async def get_count():
        # need to refetch element because may unmount on reconnect
        count = await display.page.wait_for_selector("#count")
        return await count.get_attribute("data-count")

    await display.show(SomeComponent)

    await poll(get_count).until_equals("0")
    incr = await display.page.wait_for_selector("#incr")
    await incr.click()

    await poll(get_count).until_equals("1")
    incr = await display.page.wait_for_selector("#incr")
    await incr.click()

    await poll(get_count).until_equals("2")
    incr = await display.page.wait_for_selector("#incr")
    await incr.click()

    await server.restart()

    await poll(get_count).until_equals("0")
    incr = await display.page.wait_for_selector("#incr")
    await incr.click()

    await poll(get_count).until_equals("1")
    incr = await display.page.wait_for_selector("#incr")
    await incr.click()

    await poll(get_count).until_equals("2")
    incr = await display.page.wait_for_selector("#incr")
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
                "onClick": lambda event: set_color_toggle(not color_toggle),
                "style": {"backgroundColor": color, "color": "white"},
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
        _value, set_value = reactpy.hooks.use_state("")

        async def handle_change(event):
            await asyncio.sleep(delay)
            set_value(event["target"]["value"])

        return reactpy.html.input({"onChange": handle_change, "id": "test-input"})

    await display.show(SomeComponent)

    inp = await display.page.wait_for_selector("#test-input")
    await inp.type("hello", delay=DEFAULT_TYPE_DELAY)

    assert (await inp.evaluate("node => node.value")) == "hello"
