import idom
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
