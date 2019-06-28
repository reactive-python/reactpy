import idom

# The iDOM server is running in a seperate thread so asyncio
# can't help us with synchronization problems here
from threading import Condition


def test_simple_hello_world(driver, display):
    @idom.element
    async def Hello(self):
        return idom.html.p("Hello World", id="hello")

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
            return idom.html.button("Click Me!", onClick=on_click, id="click")
        else:
            return idom.html.p("Complete", id="complete")

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
            return idom.html.input(id="input", onChange=on_change)
        else:
            return idom.html.p("Complete", id="complete")

    display(Input)

    button = driver.find_element_by_id("input")
    button.send_keys("this is a test")
    driver.find_element_by_id("complete")

    assert message.get() == "this is a test"


def test_animation(driver, display):
    count_confirmed = Condition()

    @idom.element
    async def Counter(self, count=0):

        with count_confirmed:
            count_confirmed.wait()

        @self.animate
        async def increment(stop):
            if count < 5:
                self.update(count + 1)
            else:
                stop()

        return idom.html.p(f"Count: {count}", id=f"counter-{count}")

    display(Counter)

    for i in range(6):
        with count_confirmed:
            count_confirmed.notify()
        driver.find_element_by_id(f"counter-{i}")


def test_can_prevent_event_default_operation(driver, display):
    @idom.element
    async def Input(self):
        @idom.event(preventDefault=True)
        async def on_key_down(value):
            pass

        return idom.html.input(onKeyDown=on_key_down, id="input")

    display(Input)

    inp = driver.find_element_by_id("input")
    inp.send_keys("hello")
    # the default action of updating the element's value did not take place
    assert inp.get_attribute("value") == ""


def test_can_stop_event_propogation(driver, display):
    @idom.element
    async def DivInDiv(self):
        inner_events = idom.Events()
        inner_events.on("Click", stopPropagation=True)

        async def outer_click_is_not_triggered():
            assert False

        inner = idom.html.div(
            style={"height": "30px", "width": "30px", "backgroundColor": "blue"},
            eventHandlers=inner_events,
            id="inner",
        )
        outer = idom.html.div(
            inner,
            style={"height": "35px", "width": "35px", "backgroundColor": "red"},
            onClick=outer_click_is_not_triggered,
            id="outer",
        )
        return outer

    display(DivInDiv)

    inner = driver.find_element_by_id("inner")
    inner.click()
