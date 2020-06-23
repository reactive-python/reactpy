import idom
from idom import hooks
from idom.core.events import EventHandler


def test_simple_events_object():
    events = idom.Events()

    @events.on("Click")
    async def click_handler():
        pass

    @events.on("keyPress")
    async def key_press_handler():
        pass

    assert isinstance(events["onClick"], EventHandler)
    assert isinstance(events["onKeyPress"], EventHandler)
    assert "onClick" in events
    assert "onKeyPress" in events
    assert len(events) == 2


def test_event_handler_serialization():
    assert EventHandler(target_id="uuid").serialize() == {
        "target": "uuid",
        "stopPropagation": False,
        "preventDefault": False,
    }
    assert EventHandler(target_id="uuid", prevent_default=True).serialize() == {
        "target": "uuid",
        "stopPropagation": False,
        "preventDefault": True,
    }
    assert EventHandler(target_id="uuid", stop_propagation=True).serialize() == {
        "target": "uuid",
        "stopPropagation": True,
        "preventDefault": False,
    }


async def test_multiple_callbacks_per_event_handler():
    calls = []

    event_handler = EventHandler()

    @event_handler.add
    async def callback_1(event):
        calls.append(1)

    @event_handler.add
    async def callback_2(event):
        calls.append(2)

    await event_handler([{}])

    assert calls == [1, 2]


def test_remove_event_handlers():
    def my_callback(event):
        ...

    events = EventHandler()
    events.add(my_callback)
    assert my_callback in events
    events.remove(my_callback)
    assert my_callback not in events


def test_can_prevent_event_default_operation(driver, display):
    @idom.element
    async def Input():
        @idom.event(prevent_default=True)
        async def on_key_down(value):
            pass

        return idom.html.input({"onKeyDown": on_key_down, "id": "input"})

    display(Input)

    inp = driver.find_element_by_id("input")
    inp.send_keys("hello")
    # the default action of updating the element's value did not take place
    assert inp.get_attribute("value") == ""


def test_simple_click_event(driver, display):
    clicked = idom.Var(False)

    @idom.element
    async def Button():
        update = hooks.use_update()

        async def on_click(event):
            clicked.set(True)
            update()

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


def test_can_stop_event_propogation(driver, display):
    @idom.element
    async def DivInDiv():
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
