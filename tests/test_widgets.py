import time
from base64 import b64encode
from pathlib import Path

from selenium.webdriver.common.keys import Keys

import idom
from tests.driver_utils import send_keys


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

    client_incr_button = driver.find_element_by_id("incr-button")

    driver.find_element_by_id("hotswap-1")
    client_incr_button.click()
    driver.find_element_by_id("hotswap-2")
    client_incr_button.click()
    driver.find_element_by_id("hotswap-3")


IMAGE_SRC_BYTES = b"""
<svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
    <rect width="300" height="100" style="fill:rgb(0,0,255);" />
</svg>
"""
BASE64_IMAGE_SRC = b64encode(IMAGE_SRC_BYTES).decode()


def test_image_from_string(driver, display):
    src = IMAGE_SRC_BYTES.decode()
    display(lambda: idom.widgets.image("svg", src, {"id": "a-circle-1"}))
    client_img = driver.find_element_by_id("a-circle-1")
    assert BASE64_IMAGE_SRC in client_img.get_attribute("src")


def test_image_from_bytes(driver, display):
    src = IMAGE_SRC_BYTES
    display(lambda: idom.widgets.image("svg", src, {"id": "a-circle-1"}))
    client_img = driver.find_element_by_id("a-circle-1")
    assert BASE64_IMAGE_SRC in client_img.get_attribute("src")


def test_input_callback(driver, driver_wait, display):
    inp_ref = idom.Ref(None)

    display(
        lambda: idom.widgets.Input(
            lambda value: setattr(inp_ref, "current", value),
            "text",
            "initial-value",
            {"id": "inp"},
        )
    )

    client_inp = driver.find_element_by_id("inp")
    assert client_inp.get_attribute("value") == "initial-value"

    client_inp.clear()
    send_keys(client_inp, "new-value-1")
    driver_wait.until(lambda dvr: inp_ref.current == "new-value-1")

    client_inp.clear()
    send_keys(client_inp, "new-value-2")
    driver_wait.until(lambda dvr: client_inp.get_attribute("value") == "new-value-2")


def test_input_ignore_empty(driver, driver_wait, display):
    # ignore empty since that's an invalid float
    inp_ingore_ref = idom.Ref("1")
    inp_not_ignore_ref = idom.Ref("1")

    @idom.component
    def InputWrapper():
        return idom.html.div(
            idom.widgets.Input(
                lambda value: setattr(inp_ingore_ref, "current", value),
                "number",
                inp_ingore_ref.current,
                {"id": "inp-ignore"},
                ignore_empty=True,
            ),
            idom.widgets.Input(
                lambda value: setattr(inp_not_ignore_ref, "current", value),
                "number",
                inp_not_ignore_ref.current,
                {"id": "inp-not-ignore"},
                ignore_empty=False,
            ),
        )

    display(InputWrapper)

    client_inp_ignore = driver.find_element_by_id("inp-ignore")
    client_inp_not_ignore = driver.find_element_by_id("inp-not-ignore")

    send_keys(client_inp_ignore, Keys.BACKSPACE)
    time.sleep(0.1)  # waiting and deleting again seems to decrease flakiness
    send_keys(client_inp_ignore, Keys.BACKSPACE)

    send_keys(client_inp_not_ignore, Keys.BACKSPACE)
    time.sleep(0.1)  # waiting and deleting again seems to decrease flakiness
    send_keys(client_inp_not_ignore, Keys.BACKSPACE)

    driver_wait.until(lambda drv: client_inp_ignore.get_attribute("value") == "")
    driver_wait.until(lambda drv: client_inp_not_ignore.get_attribute("value") == "")

    # ignored empty value on change
    assert inp_ingore_ref.current == "1"
    # did not ignore empty value on change
    assert inp_not_ignore_ref.current == ""
