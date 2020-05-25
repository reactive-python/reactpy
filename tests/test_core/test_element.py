import time
from queue import Queue
from threading import current_thread

import pytest
import idom


def test_element_repr():
    @idom.element
    async def MyElement(self, a):
        pass

    m_e = MyElement(1)

    assert repr(m_e) == f"test_element_repr.<locals>.MyElement({m_e.id}, a=1)"


def test_element_function_is_coroutine():
    with pytest.raises(TypeError, match="Expected a coroutine function"):

        @idom.element
        def non_coroutine_func(self):
            pass


async def test_simple_element():
    @idom.element
    async def simple_div(self):
        return idom.html.div()

    sd = simple_div()

    assert await sd.render() == {"tagName": "div"}
    # can render more than once without update
    assert await sd.render() == {"tagName": "div"}

    sd.update()
    assert await sd.render() == {"tagName": "div"}


async def test_simple_parameterized_element():
    @idom.element
    async def simple_param_element(self, tag):
        return idom.vdom(tag)

    spe = simple_param_element("div")
    assert await spe.render() == {"tagName": "div"}
    spe.update("img")
    assert await spe.render() == {"tagName": "img"}


async def test_element_with_var_args():
    @idom.element
    async def element_with_var_args_and_kwargs(self, *args, **kwargs):
        return idom.html.div(kwargs, args)

    element = element_with_var_args_and_kwargs("hello", "world", myAttr=1)

    assert (await element.render()) == {
        "tagName": "div",
        "attributes": {"myAttr": 1},
        "children": ["hello", "world"],
    }


async def test_simple_stateful_element():
    @idom.element(state="tag")
    async def simple_stateful_element(self, tag):
        return idom.vdom(tag)

    ssd = simple_stateful_element("div")
    assert await ssd.render() == {"tagName": "div"}
    ssd.update()
    assert await ssd.render() == {"tagName": "div"}
    ssd.update("img")
    assert await ssd.render() == {"tagName": "img"}
    ssd.update()
    assert await ssd.render() == {"tagName": "img"}


def test_simple_hello_world(driver, display):
    @idom.element
    async def Hello(self):
        return idom.html.p({"id": "hello"}, ["Hello World"])

    display(Hello)

    assert driver.find_element_by_id("hello")


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

    # no check mount because the element won't display till we put something in the queue
    display(Counter, check_mount=False)

    for i in range(6):
        count_queue.put(i)
        driver.find_element_by_id(f"counter-{i}")


def test_run_in_executor(driver, display):
    parent_thread = idom.Var(None)
    count_thread = idom.Var(None)

    @idom.element
    async def Main(self):
        parent_thread.set(current_thread())
        return CounterOnClick()

    @idom.element(run_in_executor=True)
    async def CounterOnClick(self, count=0):
        count_thread.set(current_thread())

        @idom.event
        async def increment(event):
            self.update(count + 1)

        return idom.html.div(
            idom.html.button(
                {"onClick": increment, "id": "button"}, "click to increment"
            ),
            idom.html.p({"id": f"count-{count}"}, f"count: {count}"),
        )

    display(Main)

    button = driver.find_element_by_id("button")

    driver.find_element_by_id("count-0")
    button.click()
    driver.find_element_by_id("count-1")

    assert parent_thread.get() != count_thread.get()


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


def test_animation_rate(driver, display):
    @idom.element
    async def Counter(self, count=0):
        @self.animate(rate=0.1)
        async def increment(stop):
            if count < 5:
                self.update(count + 1)
            else:
                stop()

        return idom.html.p({"id": f"counter-{count}"}, [f"Count: {count}"])

    start = time.time()
    display(Counter)
    driver.find_element_by_id("counter-5")
    stop = time.time()

    elapsed = stop - start
    assert elapsed > 0.5
