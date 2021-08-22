import idom
from idom.core.events import EventHandler


def test_event_handler_repr():
    handler = EventHandler(lambda: None)
    assert repr(handler) == (
        f"EventHandler(function={handler.function}, prevent_default=False, "
        f"stop_propagation=False, target={handler.target!r})"
    )


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
    @idom.component
    def Button():
        clicked, set_clicked = idom.hooks.use_state(False)

        async def on_click(event):
            set_clicked(True)

        if not clicked:
            return idom.html.button({"onClick": on_click, "id": "click"}, ["Click Me!"])
        else:
            return idom.html.p({"id": "complete"}, ["Complete"])

    display(Button)

    button = driver.find_element_by_id("click")
    button.click()
    driver.find_element_by_id("complete")


def test_can_stop_event_propogation(driver, driver_wait, display):
    clicked = idom.Ref(False)

    @idom.component
    def DivInDiv():
        @idom.event(stop_propagation=True)
        def inner_click_no_op(event):
            clicked.current = True

        def outer_click_is_not_triggered(event):
            assert False

        outer = idom.html.div(
            {
                "style": {
                    "height": "35px",
                    "width": "35px",
                    "backgroundColor": "red",
                },
                "onClick": outer_click_is_not_triggered,
                "id": "outer",
            },
            idom.html.div(
                {
                    "style": {
                        "height": "30px",
                        "width": "30px",
                        "backgroundColor": "blue",
                    },
                    "onClick": inner_click_no_op,
                    "id": "inner",
                },
            ),
        )
        return outer

    display(DivInDiv)

    inner = driver.find_element_by_id("inner")
    inner.click()

    driver_wait.until(lambda _: clicked.current)
