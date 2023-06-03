from base64 import b64encode
from pathlib import Path

import reactpy
from reactpy.testing import DisplayFixture, poll
from tests.tooling.common import DEFAULT_TYPE_DELAY

HERE = Path(__file__).parent


IMAGE_SRC_BYTES = b"""
<svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
    <rect width="300" height="100" style="fill:rgb(0,0,255);" />
</svg>
"""
BASE64_IMAGE_SRC = b64encode(IMAGE_SRC_BYTES).decode()


async def test_image_from_string(display: DisplayFixture):
    src = IMAGE_SRC_BYTES.decode()
    await display.show(lambda: reactpy.widgets.image("svg", src, {"id": "a-circle-1"}))
    client_img = await display.page.wait_for_selector("#a-circle-1")
    assert BASE64_IMAGE_SRC in (await client_img.get_attribute("src"))


async def test_image_from_bytes(display: DisplayFixture):
    src = IMAGE_SRC_BYTES
    await display.show(lambda: reactpy.widgets.image("svg", src, {"id": "a-circle-1"}))
    client_img = await display.page.wait_for_selector("#a-circle-1")
    assert BASE64_IMAGE_SRC in (await client_img.get_attribute("src"))


async def test_use_linked_inputs(display: DisplayFixture):
    @reactpy.component
    def SomeComponent():
        i_1, i_2 = reactpy.widgets.use_linked_inputs([{"id": "i_1"}, {"id": "i_2"}])
        return reactpy.html.div(i_1, i_2)

    await display.show(SomeComponent)

    input_1 = await display.page.wait_for_selector("#i_1")
    input_2 = await display.page.wait_for_selector("#i_2")

    await input_1.type("hello", delay=DEFAULT_TYPE_DELAY)

    assert (await input_1.evaluate("e => e.value")) == "hello"
    assert (await input_2.evaluate("e => e.value")) == "hello"

    await input_2.focus()
    await input_2.type(" world", delay=DEFAULT_TYPE_DELAY)

    assert (await input_1.evaluate("e => e.value")) == "hello world"
    assert (await input_2.evaluate("e => e.value")) == "hello world"


async def test_use_linked_inputs_on_change(display: DisplayFixture):
    value = reactpy.Ref(None)

    @reactpy.component
    def SomeComponent():
        i_1, i_2 = reactpy.widgets.use_linked_inputs(
            [{"id": "i_1"}, {"id": "i_2"}],
            on_change=value.set_current,
        )
        return reactpy.html.div(i_1, i_2)

    await display.show(SomeComponent)

    input_1 = await display.page.wait_for_selector("#i_1")
    input_2 = await display.page.wait_for_selector("#i_2")

    await input_1.type("hello", delay=DEFAULT_TYPE_DELAY)

    poll_value = poll(lambda: value.current)

    await poll_value.until_equals("hello")

    await input_2.focus()
    await input_2.type(" world", delay=DEFAULT_TYPE_DELAY)

    await poll_value.until_equals("hello world")


async def test_use_linked_inputs_on_change_with_cast(display: DisplayFixture):
    value = reactpy.Ref(None)

    @reactpy.component
    def SomeComponent():
        i_1, i_2 = reactpy.widgets.use_linked_inputs(
            [{"id": "i_1"}, {"id": "i_2"}], on_change=value.set_current, cast=int
        )
        return reactpy.html.div(i_1, i_2)

    await display.show(SomeComponent)

    input_1 = await display.page.wait_for_selector("#i_1")
    input_2 = await display.page.wait_for_selector("#i_2")

    await input_1.type("1")

    poll_value = poll(lambda: value.current)

    await poll_value.until_equals(1)

    await input_2.focus()
    await input_2.type("2")

    await poll_value.until_equals(12)


async def test_use_linked_inputs_ignore_empty(display: DisplayFixture):
    value = reactpy.Ref(None)

    @reactpy.component
    def SomeComponent():
        i_1, i_2 = reactpy.widgets.use_linked_inputs(
            [{"id": "i_1"}, {"id": "i_2"}],
            on_change=value.set_current,
            ignore_empty=True,
        )
        return reactpy.html.div(i_1, i_2)

    await display.show(SomeComponent)

    input_1 = await display.page.wait_for_selector("#i_1")
    input_2 = await display.page.wait_for_selector("#i_2")

    await input_1.type("1")

    poll_value = poll(lambda: value.current)

    await poll_value.until_equals("1")

    await input_2.focus()
    await input_2.press("Backspace")

    await poll_value.until_equals("1")

    await input_2.type("2")

    await poll_value.until_equals("2")
