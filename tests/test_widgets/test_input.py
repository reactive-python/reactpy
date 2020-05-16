import time
from threading import Event

import idom
from selenium.webdriver.common.keys import Keys

from tests.driver_utils import send_keys


def test_input(driver, driver_wait, display):
    inp = idom.Input("text", "initial-value", {"id": "inp"})

    display(inp)

    client_inp = driver.find_element_by_id("inp")
    assert client_inp.get_attribute("value") == "initial-value"

    client_inp.clear()
    send_keys(client_inp, "new-value-1")
    driver_wait.until(lambda dvr: inp.value == "new-value-1")

    client_inp.clear()
    send_keys(client_inp, "new-value-2")
    driver_wait.until(lambda dvr: client_inp.get_attribute("value") == "new-value-2")


def test_input_server_side_update(driver, driver_wait, display):
    @idom.element
    async def UpdateImmediately(self):
        inp = idom.Input("text", "initial-value", {"id": "inp"})
        inp.update("new-value")
        return inp

    display(UpdateImmediately)

    client_inp = driver.find_element_by_id("inp")
    driver_wait.until(lambda drv: client_inp.get_attribute("value") == "new-value")


def test_input_cast_and_ignore_empty(driver, driver_wait, display):
    # ignore empty since that's an invalid float
    change_occured = Event()

    inp = idom.Input("number", 1, {"id": "inp"}, cast=float, ignore_empty=True)

    @inp.events.on("change")
    async def on_change(event):
        change_occured.set()

    display(inp)

    client_inp = driver.find_element_by_id("inp")
    assert client_inp.get_attribute("value") == "1"

    send_keys(client_inp, Keys.BACKSPACE)
    time.sleep(0.1)  # waiting and deleting again seems to decrease flakiness
    send_keys(client_inp, Keys.BACKSPACE)

    assert change_occured.wait(timeout=3.0)
    assert client_inp.get_attribute("value") == ""
    # change ignored server side
    assert inp.value == 1

    send_keys(client_inp, "2")
    driver_wait.until(lambda drv: inp.value == 2)
