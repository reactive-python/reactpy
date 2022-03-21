import asyncio
from base64 import b64encode
from pathlib import Path

import idom
from idom.testing import DisplayFixture, poll


HERE = Path(__file__).parent


def test_multiview_repr():
    assert str(idom.widgets.MultiViewMount({})) == "MultiViewMount({})"


async def test_hostwap_update_on_change(display: DisplayFixture):
    """Ensure shared hotswapping works

    This basically means that previously rendered views of a hotswap component get updated
    when a new view is mounted, not just the next time it is re-displayed

    In this test we construct a scenario where clicking a button will cause a pre-existing
    hotswap component to be updated
    """

    def make_next_count_constructor(count):
        """We need to construct a new function so they're different when we set_state"""

        def constructor():
            count.current += 1
            return idom.html.div({"id": f"hotswap-{count.current}"}, count.current)

        return constructor

    @idom.component
    def ButtonSwapsDivs():
        count = idom.Ref(0)

        async def on_click(event):
            mount(make_next_count_constructor(count))

        incr = idom.html.button({"onClick": on_click, "id": "incr-button"}, "incr")

        mount, make_hostswap = idom.widgets.hotswap(update_on_change=True)
        mount(make_next_count_constructor(count))
        hotswap_view = make_hostswap()

        return idom.html.div(incr, hotswap_view)

    page = await display.show(ButtonSwapsDivs)

    client_incr_button = await page.wait_for_selector("#incr-button")

    await page.wait_for_selector("#hotswap-1")
    await client_incr_button.click()
    await page.wait_for_selector("#hotswap-2")
    await client_incr_button.click()
    await page.wait_for_selector("#hotswap-3")


IMAGE_SRC_BYTES = b"""
<svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
    <rect width="300" height="100" style="fill:rgb(0,0,255);" />
</svg>
"""
BASE64_IMAGE_SRC = b64encode(IMAGE_SRC_BYTES).decode()


async def test_image_from_string(display: DisplayFixture):
    src = IMAGE_SRC_BYTES.decode()
    page = await display.show(
        lambda: idom.widgets.image("svg", src, {"id": "a-circle-1"})
    )
    client_img = await page.wait_for_selector("#a-circle-1")
    assert BASE64_IMAGE_SRC in (await client_img.get_attribute("src"))


async def test_image_from_bytes(display: DisplayFixture):
    src = IMAGE_SRC_BYTES
    page = await display.show(
        lambda: idom.widgets.image("svg", src, {"id": "a-circle-1"})
    )
    client_img = await page.wait_for_selector("#a-circle-1")
    assert BASE64_IMAGE_SRC in (await client_img.get_attribute("src"))


async def test_use_linked_inputs(display: DisplayFixture):
    @idom.component
    def SomeComponent():
        i_1, i_2 = idom.widgets.use_linked_inputs([{"id": "i_1"}, {"id": "i_2"}])
        return idom.html.div(i_1, i_2)

    page = await display.show(SomeComponent)

    input_1 = await page.wait_for_selector("#i_1")
    input_2 = await page.wait_for_selector("#i_2")

    await input_1.type("hello", delay=20)

    assert (await input_1.evaluate("e => e.value")) == "hello"
    assert (await input_2.evaluate("e => e.value")) == "hello"

    await input_2.focus()
    await input_2.type(" world", delay=20)

    assert (await input_1.evaluate("e => e.value")) == "hello world"
    assert (await input_2.evaluate("e => e.value")) == "hello world"


async def test_use_linked_inputs_on_change(display: DisplayFixture):
    value = idom.Ref(None)

    @idom.component
    def SomeComponent():
        i_1, i_2 = idom.widgets.use_linked_inputs(
            [{"id": "i_1"}, {"id": "i_2"}],
            on_change=value.set_current,
        )
        return idom.html.div(i_1, i_2)

    page = await display.show(SomeComponent)

    input_1 = await page.wait_for_selector("#i_1")
    input_2 = await page.wait_for_selector("#i_2")

    await input_1.type("hello", delay=20)

    poll_value = poll(lambda: value.current)

    poll_value.until_equals("hello")

    await input_2.focus()
    await input_2.type(" world", delay=20)

    poll_value.until_equals("hello world")


async def test_use_linked_inputs_on_change_with_cast(display: DisplayFixture):
    value = idom.Ref(None)

    @idom.component
    def SomeComponent():
        i_1, i_2 = idom.widgets.use_linked_inputs(
            [{"id": "i_1"}, {"id": "i_2"}], on_change=value.set_current, cast=int
        )
        return idom.html.div(i_1, i_2)

    page = await display.show(SomeComponent)

    input_1 = await page.wait_for_selector("#i_1")
    input_2 = await page.wait_for_selector("#i_2")

    await input_1.type("1")

    poll_value = poll(lambda: value.current)

    poll_value.until_equals(1)

    await input_2.focus()
    await input_2.type("2")

    poll_value.until_equals(12)


async def test_use_linked_inputs_ignore_empty(display: DisplayFixture):
    value = idom.Ref(None)

    @idom.component
    def SomeComponent():
        i_1, i_2 = idom.widgets.use_linked_inputs(
            [{"id": "i_1"}, {"id": "i_2"}],
            on_change=value.set_current,
            ignore_empty=True,
        )
        return idom.html.div(i_1, i_2)

    page = await display.show(SomeComponent)

    input_1 = await page.wait_for_selector("#i_1")
    input_2 = await page.wait_for_selector("#i_2")

    await input_1.type("1")

    poll_value = poll(lambda: value.current)

    poll_value.until_equals("1")

    await input_2.focus()
    await input_2.press("Backspace")

    poll_value.until_equals("1")

    await input_1.type("2")

    poll_value.until_equals("2")
