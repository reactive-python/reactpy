import idom

from queue import Queue

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


def test_input(driver, driver_wait, display, driver_get):
    inp = idom.Input("text", "initial-value", {"id": "inp"})

    display(lambda: inp)

    client_inp = driver.find_element_by_id("inp")
    assert client_inp.get_attribute("value") == "initial-value"

    client_inp.clear()
    send_keys(client_inp, "new-value-1")
    driver_wait.until(lambda dvr: inp.value == "new-value-1")

    client_inp.clear()
    send_keys(client_inp, "new-value-2")
    driver_wait.until(lambda dvr: client_inp.get_attribute("value") == "new-value-2")


def test_image(driver, driver_wait, display):
    src = """
    <svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
      <rect width="300" height="100" style="fill:rgb(0,0,255);" />
    </svg>
    """
    img = idom.Image("svg", src, {"id": "a-circle"})
    display(img)
    client_img = driver.find_element_by_id("a-circle")
    assert img.base64_source in client_img.get_attribute("src")
