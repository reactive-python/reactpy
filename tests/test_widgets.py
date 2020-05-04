import time
from io import StringIO
from queue import Queue
from threading import Event

import pytest
import idom
from selenium.webdriver.common.keys import Keys

from .driver_utils import send_keys


def test_simple_hello_world(driver, display):
    @idom.element
    async def Hello(self):
        return idom.html.p({"id": "hello"}, ["Hello World"])

    display(Hello)

    assert driver.find_element_by_id("hello")


def test_simple_click_event(driver, display):
    clicked = idom.Var(False)

    @idom.element
    async def Button(self):
        async def on_click(event):
            clicked.set(True)
            self.update()

        if not clicked.get():
            return idom.html.button({"onClick": on_click, "id": "click"}, ["Click Me!"])
        else:
            return idom.html.p({"id": "complete"}, ["Complete"])

    display(Button)

    button = driver.find_element_by_id("click")
    button.click()
    driver.find_element_by_id("complete")

    # we care what happens in the final delete when there's no value
    assert clicked.get()


def test_simple_input(driver, display):
    message = idom.Var(None)

    @idom.element
    async def Input(self):
        async def on_change(event):
            if event["value"] == "this is a test":
                message.set(event["value"])
                self.update()

        if message.get() is None:
            return idom.html.input({"id": "input", "onChange": on_change})
        else:
            return idom.html.p({"id": "complete"}, ["Complete"])

    display(Input)

    button = driver.find_element_by_id("input")
    button.send_keys("this is a test")
    driver.find_element_by_id("complete")

    assert message.get() == "this is a test"


def test_animation(driver, display):
    count_queue = Queue()

    @idom.element
    async def Counter(self):

        count = count_queue.get()

        @self.animate
        async def increment(stop):
            if count < 5:
                self.update()
            else:
                stop()

        return idom.html.p({"id": f"counter-{count}"}, [f"Count: {count}"])

    display(Counter)

    for i in range(6):
        count_queue.put(i)
        driver.find_element_by_id(f"counter-{i}")


def test_can_prevent_event_default_operation(driver, display):
    @idom.element
    async def Input(self):
        @idom.event(prevent_default=True)
        async def on_key_down(value):
            pass

        return idom.html.input({"onKeyDown": on_key_down, "id": "input"})

    display(Input)

    inp = driver.find_element_by_id("input")
    inp.send_keys("hello")
    # the default action of updating the element's value did not take place
    assert inp.get_attribute("value") == ""


def test_can_stop_event_propogation(driver, display):
    @idom.element
    async def DivInDiv(self):
        inner_events = idom.Events()
        inner_events.on("Click", stop_propagation=True)

        async def outer_click_is_not_triggered():
            assert False

        inner = idom.html.div(
            {
                "style": {"height": "30px", "width": "30px", "backgroundColor": "blue"},
                "id": "inner",
            },
            event_handlers=inner_events,
        )
        outer = idom.html.div(
            {
                "style": {"height": "35px", "width": "35px", "backgroundColor": "red"},
                "onClick": outer_click_is_not_triggered,
                "id": "outer",
            },
            [inner],
        )
        return outer

    display(DivInDiv)

    inner = driver.find_element_by_id("inner")
    inner.click()


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


def test_module_deleteion():
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
