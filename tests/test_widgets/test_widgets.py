import time
from io import StringIO
from threading import Event

import pytest
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


def test_image_from_string(driver, driver_wait, display):
    src = """
    <svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
      <rect width="300" height="100" style="fill:rgb(0,0,255);" />
    </svg>
    """
    img = idom.Image("svg", src, {"id": "a-circle-1"})
    display(img)
    client_img = driver.find_element_by_id("a-circle-1")
    assert img.base64_source in client_img.get_attribute("src")

    img2 = idom.Image("svg", attributes={"id": "a-circle-2"})
    img2.io.write(src)
    display(img2)
    client_img = driver.find_element_by_id("a-circle-2")
    assert img.base64_source in client_img.get_attribute("src")


def test_image_from_bytes(driver, driver_wait, display):
    src = b"""
    <svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
      <rect width="300" height="100" style="fill:rgb(0,0,255);" />
    </svg>
    """
    img = idom.Image("svg", src, {"id": "a-circle-1"})
    display(img)
    client_img = driver.find_element_by_id("a-circle-1")
    assert img.base64_source in client_img.get_attribute("src")

    img2 = idom.Image("svg", attributes={"id": "a-circle-2"})
    img2.io.write(src)
    display(img2)
    client_img = driver.find_element_by_id("a-circle-2")
    assert img.base64_source in client_img.get_attribute("src")


def test_module_cannot_have_source_and_install():
    with pytest.raises(ValueError, match=r"Both .* were given."):
        idom.Module("something", install="something", source=StringIO())


def test_module_deletion():
    # also test install
    jquery = idom.Module("jquery", install="jquery@3.5.0")
    assert idom.client.web_module_exists(jquery.name)
    with idom.client.web_module_path(jquery.name).open() as f:
        assert "jQuery JavaScript Library v3.5.0" in f.read()
    jquery.delete()
    assert not idom.client.web_module_exists(jquery.name)


def test_module_from_url():
    url = "https://code.jquery.com/jquery-3.5.0.js"
    jquery = idom.Module(url)
    assert jquery.url == url
    with pytest.raises(ValueError, match="Module is not installed locally"):
        jquery.name
    with pytest.raises(ValueError, match="Module is not installed locally"):
        jquery.delete()
