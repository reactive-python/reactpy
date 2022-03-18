from base64 import b64encode
from pathlib import Path

from selenium.webdriver.common.keys import Keys

import idom
from tests.utils.browser import send_keys


HERE = Path(__file__).parent


def test_multiview_repr():
    assert str(idom.widgets.MultiViewMount({})) == "MultiViewMount({})"


def test_hostwap_update_on_change(driver, display):
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

    display(ButtonSwapsDivs)

    client_incr_button = driver.find_element("id", "incr-button")

    driver.find_element("id", "hotswap-1")
    client_incr_button.click()
    driver.find_element("id", "hotswap-2")
    client_incr_button.click()
    driver.find_element("id", "hotswap-3")


IMAGE_SRC_BYTES = b"""
<svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
    <rect width="300" height="100" style="fill:rgb(0,0,255);" />
</svg>
"""
BASE64_IMAGE_SRC = b64encode(IMAGE_SRC_BYTES).decode()


def test_image_from_string(driver, display):
    src = IMAGE_SRC_BYTES.decode()
    display(lambda: idom.widgets.image("svg", src, {"id": "a-circle-1"}))
    client_img = driver.find_element("id", "a-circle-1")
    assert BASE64_IMAGE_SRC in client_img.get_attribute("src")


def test_image_from_bytes(driver, display):
    src = IMAGE_SRC_BYTES
    display(lambda: idom.widgets.image("svg", src, {"id": "a-circle-1"}))
    client_img = driver.find_element("id", "a-circle-1")
    assert BASE64_IMAGE_SRC in client_img.get_attribute("src")


def test_use_linked_inputs(driver, driver_wait, display):
    @idom.component
    def SomeComponent():
        i_1, i_2 = idom.widgets.use_linked_inputs([{"id": "i_1"}, {"id": "i_2"}])
        return idom.html.div(i_1, i_2)

    display(SomeComponent)

    input_1 = driver.find_element("id", "i_1")
    input_2 = driver.find_element("id", "i_2")

    send_keys(input_1, "hello")

    driver_wait.until(lambda d: input_1.get_attribute("value") == "hello")
    driver_wait.until(lambda d: input_2.get_attribute("value") == "hello")

    send_keys(input_2, " world")

    driver_wait.until(lambda d: input_1.get_attribute("value") == "hello world")
    driver_wait.until(lambda d: input_2.get_attribute("value") == "hello world")


def test_use_linked_inputs_on_change(driver, driver_wait, display):
    value = idom.Ref(None)

    @idom.component
    def SomeComponent():
        i_1, i_2 = idom.widgets.use_linked_inputs(
            [{"id": "i_1"}, {"id": "i_2"}],
            on_change=value.set_current,
        )
        return idom.html.div(i_1, i_2)

    display(SomeComponent)

    input_1 = driver.find_element("id", "i_1")
    input_2 = driver.find_element("id", "i_2")

    send_keys(input_1, "hello")

    driver_wait.until(lambda d: value.current == "hello")

    send_keys(input_2, " world")

    driver_wait.until(lambda d: value.current == "hello world")


def test_use_linked_inputs_on_change_with_cast(driver, driver_wait, display):
    value = idom.Ref(None)

    @idom.component
    def SomeComponent():
        i_1, i_2 = idom.widgets.use_linked_inputs(
            [{"id": "i_1"}, {"id": "i_2"}], on_change=value.set_current, cast=int
        )
        return idom.html.div(i_1, i_2)

    display(SomeComponent)

    input_1 = driver.find_element("id", "i_1")
    input_2 = driver.find_element("id", "i_2")

    send_keys(input_1, "1")

    driver_wait.until(lambda d: value.current == 1)

    send_keys(input_2, "2")

    driver_wait.until(lambda d: value.current == 12)


def test_use_linked_inputs_ignore_empty(driver, driver_wait, display):
    value = idom.Ref(None)

    @idom.component
    def SomeComponent():
        i_1, i_2 = idom.widgets.use_linked_inputs(
            [{"id": "i_1"}, {"id": "i_2"}],
            on_change=value.set_current,
            ignore_empty=True,
        )
        return idom.html.div(i_1, i_2)

    display(SomeComponent)

    input_1 = driver.find_element("id", "i_1")
    input_2 = driver.find_element("id", "i_2")

    send_keys(input_1, "1")

    driver_wait.until(lambda d: value.current == "1")

    send_keys(input_2, Keys.BACKSPACE)

    assert value.current == "1"

    send_keys(input_1, "2")

    driver_wait.until(lambda d: value.current == "2")
