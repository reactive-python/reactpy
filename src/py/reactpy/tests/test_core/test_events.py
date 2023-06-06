import pytest

import reactpy
from reactpy.core.events import (
    EventHandler,
    merge_event_handler_funcs,
    merge_event_handlers,
    to_event_handler_function,
)
from reactpy.testing import DisplayFixture, poll
from tests.tooling.common import DEFAULT_TYPE_DELAY


def test_event_handler_repr():
    handler = EventHandler(lambda: None)
    assert repr(handler) == (
        f"EventHandler(function={handler.function}, prevent_default=False, "
        f"stop_propagation=False, target={handler.target!r})"
    )


def test_event_handler_props():
    handler_0 = EventHandler(lambda data: None)
    assert handler_0.stop_propagation is False
    assert handler_0.prevent_default is False
    assert handler_0.target is None

    handler_1 = EventHandler(lambda data: None, prevent_default=True)
    assert handler_1.stop_propagation is False
    assert handler_1.prevent_default is True
    assert handler_1.target is None

    handler_2 = EventHandler(lambda data: None, stop_propagation=True)
    assert handler_2.stop_propagation is True
    assert handler_2.prevent_default is False
    assert handler_2.target is None

    handler_3 = EventHandler(lambda data: None, target="123")
    assert handler_3.stop_propagation is False
    assert handler_3.prevent_default is False
    assert handler_3.target == "123"


def test_event_handler_equivalence():
    async def func(data):
        return None

    assert EventHandler(func) == EventHandler(func)

    assert EventHandler(lambda data: None) != EventHandler(lambda data: None)

    assert EventHandler(func, stop_propagation=True) != EventHandler(
        func, stop_propagation=False
    )

    assert EventHandler(func, prevent_default=True) != EventHandler(
        func, prevent_default=False
    )

    assert EventHandler(func, target="123") != EventHandler(func, target="456")


async def test_to_event_handler_function():
    call_args = reactpy.Ref(None)

    async def coro(*args):
        call_args.current = args

    def func(*args):
        call_args.current = args

    await to_event_handler_function(coro, positional_args=True)([1, 2, 3])
    assert call_args.current == (1, 2, 3)

    await to_event_handler_function(func, positional_args=True)([1, 2, 3])
    assert call_args.current == (1, 2, 3)

    await to_event_handler_function(coro, positional_args=False)([1, 2, 3])
    assert call_args.current == ([1, 2, 3],)

    await to_event_handler_function(func, positional_args=False)([1, 2, 3])
    assert call_args.current == ([1, 2, 3],)


async def test_merge_event_handler_empty_list():
    with pytest.raises(ValueError, match="No event handlers to merge"):
        merge_event_handlers([])


@pytest.mark.parametrize(
    "kwargs_1, kwargs_2",
    [
        ({"stop_propagation": True}, {"stop_propagation": False}),
        ({"prevent_default": True}, {"prevent_default": False}),
        ({"target": "this"}, {"target": "that"}),
    ],
)
async def test_merge_event_handlers_raises_on_mismatch(kwargs_1, kwargs_2):
    def func(data):
        return None

    with pytest.raises(ValueError, match="Cannot merge handlers"):
        merge_event_handlers(
            [
                EventHandler(func, **kwargs_1),
                EventHandler(func, **kwargs_2),
            ]
        )


async def test_merge_event_handlers():
    handler = EventHandler(lambda data: None)
    assert merge_event_handlers([handler]) is handler

    calls = []
    merged_handler = merge_event_handlers(
        [
            EventHandler(lambda data: calls.append("first")),
            EventHandler(lambda data: calls.append("second")),
        ]
    )
    await merged_handler.function({})
    assert calls == ["first", "second"]


def test_merge_event_handler_funcs_empty_list():
    with pytest.raises(ValueError, match="No event handler functions to merge"):
        merge_event_handler_funcs([])


async def test_merge_event_handler_funcs():
    calls = []

    async def some_func(data):
        calls.append("some_func")

    async def some_other_func(data):
        calls.append("some_other_func")

    assert merge_event_handler_funcs([some_func]) is some_func

    merged_handler = merge_event_handler_funcs([some_func, some_other_func])
    await merged_handler([])
    assert calls == ["some_func", "some_other_func"]


async def test_can_prevent_event_default_operation(display: DisplayFixture):
    @reactpy.component
    def Input():
        @reactpy.event(prevent_default=True)
        async def on_key_down(value):
            pass

        return reactpy.html.input({"on_key_down": on_key_down, "id": "input"})

    await display.show(Input)

    inp = await display.page.wait_for_selector("#input")
    await inp.type("hello", delay=DEFAULT_TYPE_DELAY)
    # the default action of updating the element's value did not take place
    assert (await inp.evaluate("node => node.value")) == ""


async def test_simple_click_event(display: DisplayFixture):
    @reactpy.component
    def Button():
        clicked, set_clicked = reactpy.hooks.use_state(False)

        async def on_click(event):
            set_clicked(True)

        if not clicked:
            return reactpy.html.button(
                {"on_click": on_click, "id": "click"}, ["Click Me!"]
            )
        else:
            return reactpy.html.p({"id": "complete"}, ["Complete"])

    await display.show(Button)

    button = await display.page.wait_for_selector("#click")
    await button.click()
    await display.page.wait_for_selector("#complete")


async def test_can_stop_event_propagation(display: DisplayFixture):
    clicked = reactpy.Ref(False)

    @reactpy.component
    def DivInDiv():
        @reactpy.event(stop_propagation=True)
        def inner_click_no_op(event):
            clicked.current = True

        def outer_click_is_not_triggered(event):
            raise AssertionError()

        outer = reactpy.html.div(
            {
                "style": {"height": "35px", "width": "35px", "background_color": "red"},
                "on_click": outer_click_is_not_triggered,
                "id": "outer",
            },
            reactpy.html.div(
                {
                    "style": {
                        "height": "30px",
                        "width": "30px",
                        "background_color": "blue",
                    },
                    "on_click": inner_click_no_op,
                    "id": "inner",
                }
            ),
        )
        return outer

    await display.show(DivInDiv)

    inner = await display.page.wait_for_selector("#inner")
    await inner.click()

    await poll(lambda: clicked.current).until_is(True)
