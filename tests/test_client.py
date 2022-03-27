import asyncio
import time
from contextlib import AsyncExitStack
from pathlib import Path

from playwright.async_api import Browser

import idom
from idom.testing import DisplayFixture, ServerFixture


JS_DIR = Path(__file__).parent / "js"


async def test_automatic_reconnect(browser: Browser):
    page = await browser.new_page()

    # we need to wait longer here because the automatic reconnect is not instant
    page.set_default_timeout(10000)

    @idom.component
    def OldComponent():
        return idom.html.p({"id": "old-component"}, "old")

    async with AsyncExitStack() as exit_stack:
        server = await exit_stack.enter_async_context(ServerFixture(port=8000))
        display = await exit_stack.enter_async_context(
            DisplayFixture(server, driver=page)
        )

        await display.show(OldComponent)

        # ensure the element is displayed before stopping the server
        await page.wait_for_selector("#old-component")

    # the server is disconnected but the last view state is still shown
    await page.wait_for_selector("#old-component")

    set_state = idom.Ref(None)

    @idom.component
    def NewComponent():
        state, set_state.current = idom.hooks.use_state(0)
        return idom.html.p({"id": f"new-component-{state}"}, f"new-{state}")

    async with AsyncExitStack() as exit_stack:
        server = await exit_stack.enter_async_context(ServerFixture(port=8000))
        display = await exit_stack.enter_async_context(
            DisplayFixture(server, driver=page)
        )

        await display.show(NewComponent)

        # Note the lack of a page refresh before looking up this new component. The
        # client should attempt to reconnect and display the new view automatically.
        await page.wait_for_selector("#new-component-0")

        # check that we can resume normal operation
        set_state.current(1)
        await page.wait_for_selector("#new-component-1")


def test_style_can_be_changed(display, driver, driver_wait):
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
            {
                "id": "my-button",
                "onClick": lambda event: set_color_toggle(not color_toggle),
                "style": {"backgroundColor": color, "color": "white"},
            },
            f"color: {color}",
        )

    display(ButtonWithChangingColor)

    button = driver.find_element("id", "my-button")

    assert _get_style(button)["background-color"] == "red"

    for color in ["blue", "red"] * 2:
        button.click()
        driver_wait.until(lambda _: _get_style(button)["background-color"] == color)


def _get_style(element):
    items = element.get_attribute("style").split(";")
    pairs = [item.split(":", 1) for item in map(str.strip, items) if item]
    return {key.strip(): value.strip() for key, value in pairs}


def test_slow_server_response_on_input_change(display, driver, driver_wait):
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

        return idom.html.input({"onChange": handle_change, "id": "test-input"})

    display(SomeComponent)

    inp = driver.find_element("id", "test-input")

    text = "hello"
    send_keys(inp, text)

    time.sleep(delay * len(text) * 1.1)

    driver_wait.until(lambda _: inp.get_attribute("value") == "hello")
