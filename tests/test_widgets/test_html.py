import time
from base64 import b64encode

from selenium.webdriver.common.keys import Keys

import idom
from tests.driver_utils import send_keys


_image_src_bytes = b"""
<svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
    <rect width="300" height="100" style="fill:rgb(0,0,255);" />
</svg>
"""
_base64_image_src = b64encode(_image_src_bytes).decode()


def test_image_from_string(driver, display):
    src = _image_src_bytes.decode()
    display(lambda: idom.widgets.image("svg", src, {"id": "a-circle-1"}))
    client_img = driver.find_element_by_id("a-circle-1")
    assert _base64_image_src in client_img.get_attribute("src")


def test_image_from_bytes(driver, display):
    src = _image_src_bytes
    display(lambda: idom.widgets.image("svg", src, {"id": "a-circle-1"}))
    client_img = driver.find_element_by_id("a-circle-1")
    assert _base64_image_src in client_img.get_attribute("src")


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
