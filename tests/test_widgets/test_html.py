from base64 import b64encode
import time

import idom
from selenium.webdriver.common.keys import Keys

from tests.driver_utils import send_keys


_image_src_bytes = b"""
<svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
    <rect width="300" height="100" style="fill:rgb(0,0,255);" />
</svg>
"""
_base64_image_src = b64encode(_image_src_bytes).decode()


def test_image_from_string(driver, driver_wait, display):
    src = _image_src_bytes.decode()
    img = idom.widgets.image("svg", src, {"id": "a-circle-1"})
    display(img)
    client_img = driver.find_element_by_id("a-circle-1")
    assert _base64_image_src in client_img.get_attribute("src")


def test_image_from_bytes(driver, driver_wait, display):
    src = _image_src_bytes
    img = idom.widgets.image("svg", src, {"id": "a-circle-1"})
    display(img)
    client_img = driver.find_element_by_id("a-circle-1")
    assert _base64_image_src in client_img.get_attribute("src")


def test_input_callback(driver, driver_wait, display):
    inp_var = idom.Var(None)
    inp = idom.widgets.Input(
        "text", "initial-value", {"id": "inp"}, callback=inp_var.set,
    )

    display(inp)

    client_inp = driver.find_element_by_id("inp")
    assert client_inp.get_attribute("value") == "initial-value"

    client_inp.clear()
    send_keys(client_inp, "new-value-1")
    driver_wait.until(lambda dvr: inp_var.value == "new-value-1")

    client_inp.clear()
    send_keys(client_inp, "new-value-2")
    driver_wait.until(lambda dvr: client_inp.get_attribute("value") == "new-value-2")


def test_input_server_side_update(driver, driver_wait, display):
    @idom.element
    async def UpdateImmediately():
        value, set_value = idom.hooks.use_state("initial-value")
        inp = idom.widgets.Input("text", value, {"id": "inp"})
        set_value("new-value")
        return inp

    display(UpdateImmediately)

    client_inp = driver.find_element_by_id("inp")
    driver_wait.until(lambda drv: client_inp.get_attribute("value") == "new-value")


def test_input_ignore_empty(driver, driver_wait, display):
    # ignore empty since that's an invalid float
    inp_ingore_var = idom.Var("1")
    inp_not_ignore_var = idom.Var("1")

    @idom.element
    async def InputWrapper():
        return idom.html.div(
            idom.widgets.Input(
                "number",
                inp_ingore_var.value,
                {"id": "inp-ignore"},
                callback=inp_ingore_var.set,
                ignore_empty=True,
            ),
            idom.widgets.Input(
                "number",
                inp_not_ignore_var.value,
                {"id": "inp-not-ignore"},
                callback=inp_not_ignore_var.set,
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
    assert inp_ingore_var.value == "1"
    # did not ignore empty value on change
    assert inp_not_ignore_var.value == ""
