import idom
from idom import hooks
from idom.core.events import EventHandler


def test_event_handler_repr():
    handler = EventHandler(lambda: None)
    assert repr(handler) == (
        f"EventHandler(function={handler.function}, prevent_default=False, "
        f"stop_propagation=False, target={handler.target!r})"
    )


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


async def test_register_multiple_handlers_to_same_event():
    events = idom.Events()

    calls = []

    @events.on("change")
    async def handler_1():
        calls.append(1)

    @events.on("change")
    async def handler_2():
        calls.append(2)

    await events["onChange"].function([])

    assert calls == [1, 2]


def test_event_handler_props():
    handler_0 = EventHandler(lambda: None)
    assert handler_0.stop_propagation is False
    assert handler_0.prevent_default is False

    handler_1 = EventHandler(lambda: None, prevent_default=True)
    assert handler_1.stop_propagation is False
    assert handler_1.prevent_default is True

    handler_2 = EventHandler(lambda: None, stop_propagation=True)
    assert handler_2.stop_propagation is True
    assert handler_2.prevent_default is False


def test_to_event_handler_function():
    assert False


def test_merge_event_handlers():
    assert False


def test_merge_event_handler_funcs():
    assert False


def test_can_prevent_event_default_operation(driver, display):
    @idom.component
    def Input():
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
    clicked = idom.Ref(False)

    @idom.component
    def Button():
        hook = hooks.current_hook()

        async def on_click(event):
            clicked.current = True
            hook.schedule_render()

        if not clicked.current:
            return idom.html.button({"onClick": on_click, "id": "click"}, ["Click Me!"])
        else:
            return idom.html.p({"id": "complete"}, ["Complete"])

    display(Button)

    button = driver.find_element_by_id("click")
    button.click()
    driver.find_element_by_id("complete")

    # we care what happens in the final delete when there's no value
    assert clicked.current


def test_can_stop_event_propogation(driver, display):
    @idom.component
    def DivInDiv():
        inner_events = idom.Events()
        inner_events.on("Click", stop_propagation=True)

        async def outer_click_is_not_triggered(event):
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
        print(inner["eventHandlers"])
        return outer

    display(DivInDiv)

    inner = driver.find_element_by_id("inner")
    inner.click()
