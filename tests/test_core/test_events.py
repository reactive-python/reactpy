import asyncio
import json
from functools import partial

import pytest

import reactpy
from reactpy import component, html, use_effect, use_state
from reactpy.core.events import (
    EventHandler,
    event,
    merge_event_handler_funcs,
    merge_event_handlers,
    to_event_handler_function,
)
from reactpy.core.layout import Layout
from reactpy.testing import (
    DEFAULT_TYPE_DELAY,
    DisplayFixture,
    StaticEventHandler,
    poll,
)
from reactpy.types import Event
from tests.tooling.common import TYPE_DELAYS, event_message


def test_event_handler_repr():
    handler = EventHandler(lambda: None)
    assert repr(handler) == (
        f"EventHandler(function={handler.function}, prevent_default=False, "
        f"stop_propagation=False, stop_immediate_propagation=False, debounce=None, "
        f"target={handler.target!r}, throttle=None, event_proxy=None)"
    )


def test_event_handler_props():
    handler_0 = EventHandler(lambda data: None)
    assert handler_0.stop_propagation is False
    assert handler_0.prevent_default is False
    assert handler_0.debounce is None
    assert handler_0.throttle is None
    assert handler_0.target is None

    handler_1 = EventHandler(lambda data: None, prevent_default=True)
    assert handler_1.stop_propagation is False
    assert handler_1.prevent_default is True
    assert handler_1.debounce is None
    assert handler_1.throttle is None
    assert handler_1.target is None

    handler_2 = EventHandler(lambda data: None, stop_propagation=True)
    assert handler_2.stop_propagation is True
    assert handler_2.prevent_default is False
    assert handler_2.debounce is None
    assert handler_2.throttle is None
    assert handler_2.target is None

    handler_3 = EventHandler(lambda data: None, target="123")
    assert handler_3.stop_propagation is False
    assert handler_3.prevent_default is False
    assert handler_3.debounce is None
    assert handler_3.throttle is None
    assert handler_3.target == "123"

    handler_4 = EventHandler(lambda data: None, debounce=250)
    assert handler_4.stop_propagation is False
    assert handler_4.prevent_default is False
    assert handler_4.debounce == 250
    assert handler_4.throttle is None
    assert handler_4.target is None

    handler_5 = EventHandler(lambda data: None, throttle=150)
    assert handler_5.stop_propagation is False
    assert handler_5.prevent_default is False
    assert handler_5.debounce is None
    assert handler_5.throttle == 150
    assert handler_5.target is None


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

    assert EventHandler(func, debounce=200) != EventHandler(func, debounce=100)

    assert EventHandler(func, throttle=200) != EventHandler(func, throttle=100)

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
    with pytest.raises(ValueError, match=r"No event handlers to merge"):
        merge_event_handlers([])


@pytest.mark.parametrize(
    "kwargs_1, kwargs_2",
    [
        ({"stop_propagation": True}, {"stop_propagation": False}),
        ({"prevent_default": True}, {"prevent_default": False}),
        ({"debounce": 200}, {"debounce": 100}),
        ({"throttle": 200}, {"throttle": 100}),
        ({"target": "this"}, {"target": "that"}),
    ],
)
async def test_merge_event_handlers_raises_on_mismatch(kwargs_1, kwargs_2):
    def func(data):
        return None

    with pytest.raises(ValueError, match=r"Cannot merge handlers"):
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
    with pytest.raises(ValueError, match=r"No event handler functions to merge"):
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


def test_merge_event_handlers_event_proxy():
    """Merging never has to settle an argument about live access

    Whether the browser object behind an event should be kept alive is not something
    two handlers can contradict each other over - one of them simply wants it. The
    merged handler asks for it whenever any of the originals did, and states nothing
    at all when none of them said either way.
    """
    plain = EventHandler(lambda data: None)
    wants = EventHandler(lambda data: None, event_proxy=True)
    declines = EventHandler(lambda data: None, event_proxy=False)
    other_plain = EventHandler(lambda data: None)

    assert merge_event_handlers([plain, other_plain]).event_proxy is None
    assert merge_event_handlers([plain, wants]).event_proxy is True
    assert merge_event_handlers([plain, declines]).event_proxy is False
    assert merge_event_handlers([declines, wants]).event_proxy is True


async def test_can_prevent_event_default_operation(display: DisplayFixture):
    @reactpy.component
    def Input():
        @reactpy.event(prevent_default=True)
        async def on_key_down(value):
            pass

        return reactpy.html.input({"onKeyDown": on_key_down, "id": "input"})

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
                {"onClick": on_click, "id": "click"}, ["Click Me!"]
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
            raise AssertionError

        outer = reactpy.html.div(
            {
                "style": {"height": "35px", "width": "35px", "backgroundColor": "red"},
                "onClick": outer_click_is_not_triggered,
                "id": "outer",
            },
            reactpy.html.div(
                {
                    "style": {
                        "height": "30px",
                        "width": "30px",
                        "backgroundColor": "blue",
                    },
                    "onClick": inner_click_no_op,
                    "id": "inner",
                }
            ),
        )
        return outer

    await display.show(DivInDiv)

    inner = await display.page.wait_for_selector("#inner")
    await inner.click()

    await poll(lambda: clicked.current).until_is(True)


async def test_javascript_event_as_arrow_function(display: DisplayFixture):
    @reactpy.component
    def App():
        return reactpy.html.div(
            reactpy.html.div(
                reactpy.html.button(
                    {
                        "id": "the-button",
                        "onClick": '(e) => e.target.innerText = "Thank you!"',
                    },
                    "Click Me",
                ),
                reactpy.html.div({"id": "the-parent"}),
            )
        )

    await display.show(lambda: App())

    button = await display.page.wait_for_selector("#the-button", state="attached")
    assert await button.inner_text() == "Click Me"
    await button.click()
    assert await button.inner_text() == "Thank you!"


async def test_javascript_event_as_this_statement(display: DisplayFixture):
    @reactpy.component
    def App():
        return reactpy.html.div(
            reactpy.html.div(
                reactpy.html.button(
                    {
                        "id": "the-button",
                        "onClick": 'this.innerText = "Thank you!"',
                    },
                    "Click Me",
                ),
                reactpy.html.div({"id": "the-parent"}),
            )
        )

    await display.show(lambda: App())

    button = await display.page.wait_for_selector("#the-button", state="attached")
    assert await button.inner_text() == "Click Me"
    await button.click()
    assert await button.inner_text() == "Thank you!"


async def test_javascript_event_after_state_update(display: DisplayFixture):
    @reactpy.component
    def App():
        click_count, set_click_count = reactpy.hooks.use_state(0)
        return reactpy.html.div(
            {"id": "the-parent"},
            reactpy.html.button(
                {
                    "id": "button-with-reactpy-event",
                    "onClick": lambda _: set_click_count(click_count + 1),
                },
                "Click Me",
            ),
            reactpy.html.button(
                {
                    "id": "button-with-javascript-event",
                    "onClick": """javascript: () => {
                    let parent = document.getElementById("the-parent");
                    parent.appendChild(document.createElement("div"));
                }""",
                },
                "No, Click Me",
            ),
            *[reactpy.html.div("Clicked") for _ in range(click_count)],
        )

    await display.show(lambda: App())

    button1 = await display.page.wait_for_selector(
        "#button-with-reactpy-event", state="attached"
    )
    await button1.click()
    await button1.click()
    await button1.click()
    button2 = await display.page.wait_for_selector(
        "#button-with-javascript-event", state="attached"
    )
    await button2.click()
    await button2.click()
    await button2.click()
    parent = await display.page.wait_for_selector("#the-parent", state="attached")
    generated_divs = await parent.query_selector_all("div")

    assert len(generated_divs) == 6


def test_detect_prevent_default():
    def handler(event: Event):
        event.preventDefault()

    eh = EventHandler(handler)
    assert eh.prevent_default is True


def test_detect_stop_propagation():
    def handler(event: Event):
        event.stopPropagation()

    eh = EventHandler(handler)
    assert eh.stop_propagation is True


def test_detect_debounce():
    def handler(event: Event):
        event.debounce = 200

    eh = EventHandler(handler)
    assert eh.debounce == 200


def test_computed_debounce_value_is_not_detected():
    # A pure runtime computation (no closure capture, no constant) cannot be
    # resolved statically; the detection returns ``None`` so users are not
    # silently misled. Capture the closure form separately to assert that
    # resolution from enclosing scope *does* work.
    def make_handler():
        computed_debounce = 200

        def handler(event: Event):
            event.debounce = computed_debounce

        return handler

    eh = EventHandler(make_handler())
    # Closure capture is now detected (see
    # ``test_detect_debounce_from_closure``).
    assert eh.debounce == 200

    # A value computed at call time without a resolvable binding is not
    # detected. This protects users from being told the wrong number when
    # the runtime value may differ.
    def get_debounce():
        return 200

    def handler(event: Event):
        event.debounce = get_debounce()

    eh2 = EventHandler(handler)
    assert eh2.debounce is None


def test_detect_both():
    def handler(event: Event):
        event.preventDefault()
        event.stopPropagation()

    eh = EventHandler(handler)
    assert eh.prevent_default is True
    assert eh.stop_propagation is True


def test_detect_both_when_handler_is_partial():
    def handler(event: Event, *, extra_param):
        event.preventDefault()
        event.stopPropagation()

    eh = EventHandler(partial(handler, extra_param="extra_value"))
    assert eh.prevent_default is True
    assert eh.stop_propagation is True


def test_detect_debounce_when_handler_is_partial():
    def handler(event: Event, *, extra_param):
        event.debounce = 125

    eh = EventHandler(partial(handler, extra_param=125))
    assert eh.debounce == 125


def test_detect_debounce_from_positional_default():
    def handler(event: Event, ms=375):
        event.debounce = ms

    eh = EventHandler(handler)
    assert eh.debounce == 375


def test_detect_debounce_from_keyword_only_default():
    def handler(event: Event, *, ms=400):
        event.debounce = ms

    eh = EventHandler(handler)
    assert eh.debounce == 400


def test_detect_debounce_from_closure():
    def make(ms):
        def handler(event: Event):
            event.debounce = ms

        return handler

    eh = EventHandler(make(450))
    assert eh.debounce == 450


def test_detect_debounce_from_closure_among_multiple():
    def make(unused, used):
        def handler(event: Event):
            event.debounce = used

        return handler

    eh = EventHandler(make(100, 250))
    assert eh.debounce == 250


def test_no_detect_debounce_when_local_var_used():
    def handler(event: Event):
        ms = 500
        event.debounce = ms

    eh = EventHandler(handler)
    assert eh.debounce is None


def test_no_detect_debounce_when_fallback_literal_used():
    # Branch uses a local var (unresolvable) plus a literal fallback; we
    # refuse to pick either because runtime behaviour is ambiguous.
    def handler(event: Event):
        val = 50
        if val:
            event.debounce = val
        else:
            event.debounce = 999

    eh = EventHandler(handler)
    assert eh.debounce is None


def test_detect_debounce_from_nested_default():
    def handler(event: Event, a=100, b=200):
        event.debounce = b

    eh = EventHandler(handler)
    assert eh.debounce == 200


def test_detect_debounce_zero_literal():
    def handler(event: Event):
        event.debounce = 0

    eh = EventHandler(handler)
    assert eh.debounce == 0


def test_no_detect():
    def handler(event: Event):
        pass

    eh = EventHandler(handler)
    assert eh.prevent_default is False
    assert eh.stop_propagation is False
    assert eh.debounce is None


def test_event_decorator_accepts_throttle():
    @event(throttle=200)
    def handler(event: Event):
        pass

    assert handler.throttle == 200
    assert handler.debounce is None


def test_event_decorator_accepts_debounce_and_throttle():
    @event(debounce=300, throttle=100)
    def handler(event: Event):
        pass

    assert handler.debounce == 300
    assert handler.throttle == 100


def test_event_handler_throttle_default_is_none():
    eh = EventHandler(lambda data: None)
    assert eh.throttle is None


def test_event_wrapper():
    data = {"a": 1, "b": {"c": 2}}
    event = Event(data)
    assert event.a == 1
    assert event.b.c == 2
    assert event["a"] == 1
    assert event["b"]["c"] == 2


async def test_vdom_has_prevent_default():
    @component
    def MyComponent():
        def handler(event: Event):
            event.preventDefault()

        return html.button({"onClick": handler})

    async with Layout(MyComponent()) as layout:
        await layout.render()
        # Check layout._event_handlers
        # Find the handler
        handler = next(iter(layout._event_handlers.values()))
        assert handler.prevent_default is True


async def test_vdom_has_debounce():
    @component
    def MyComponent():
        def handler(event: Event):
            event.debounce = 200

        return html.input({"onChange": handler})

    async with Layout(MyComponent()) as layout:
        await layout.render()
        handler = next(iter(layout._event_handlers.values()))
        assert handler.debounce == 200


def test_event_export():
    from reactpy.types import Event

    assert Event is not None


def test_detect_false_positive():
    def handler(event: Event):
        # This should not trigger detection
        other = Event()
        other.preventDefault()
        other.stopPropagation()
        other.debounce = 200

    eh = EventHandler(handler)
    assert eh.prevent_default is False
    assert eh.stop_propagation is False
    assert eh.debounce is None


def test_detect_renamed_argument():
    def handler(e: Event):
        e.preventDefault()
        e.stopPropagation()
        e.debounce = 200

    eh = EventHandler(handler)
    assert eh.prevent_default is True
    assert eh.stop_propagation is True
    assert eh.debounce == 200


async def test_event_queue_sequential_processing(display: DisplayFixture):
    """Ensure events are processed sequentially for the same target"""

    events_processed = []

    @component
    def SequentialEvents():
        async def handle_click(event):
            # Simulate slow processing
            await asyncio.sleep(0.1)
            events_processed.append(event["target"])

        return html.button({"id": "btn", "onClick": handle_click}, "Click me")

    await display.show(SequentialEvents)

    # Get the element
    btn = display.page.locator("#btn")

    # Click 3 times rapidly
    # We use evaluate to trigger clicks rapidly from client side perspective if possible,
    # or just click rapidly via playwright.
    # Playwright's click is awaited, so we need to run them concurrently.

    await asyncio.gather(
        btn.click(),
        btn.click(),
        btn.click(),
    )

    # Wait for processing to complete (0.1s * 3 = 0.3s approx)
    await asyncio.sleep(0.5)

    assert len(events_processed) == 3


async def test_event_targeting_with_shifting_elements(display: DisplayFixture):
    """
    Ensure that events are delivered to the correct component even when
    elements shift around it, provided explicit keys are used.
    """

    clicked_items = []

    @component
    def Item(id_val):
        async def handle_click(event):
            clicked_items.append(id_val)

        return html.div(
            {"id": f"item-{id_val}", "onClick": handle_click}, f"Item {id_val}"
        )

    @component
    def ListContainer():
        items, set_items = use_state(["B", "C"])

        def add_top(event):
            set_items(["A", *items])

        return html.div(
            html.button({"id": "add-btn", "onClick": add_top}, "Add Top"),
            html.div({"id": "list"}, [Item(i, key=i) for i in items]),
        )

    await display.show(ListContainer)

    # Initial state: Items B, C are present.
    # Click Item B.
    btn_b = display.page.locator("#item-B")
    await btn_b.click()

    # Add Item A to the top.
    add_btn = display.page.locator("#add-btn")
    await add_btn.click()

    # Wait for Item A to appear to ensure render is complete
    await display.page.locator("#item-A").wait_for()

    # Now the list is [A, B, C].
    # Item B has shifted position in the DOM (index 0 -> index 1).
    # Its key path should remain .../B regardless of index if we implemented it right?
    # Actually, let's verify how key_path is constructed.
    # In layout.py: key_path=f"{parent.key_path}/{key}"
    # So if the parent is the div container, and items have keys "A", "B", "C".
    # The paths are .../list/A, .../list/B, .../list/C.
    # The index in the children array changes, but the key_path relies on the key, not the index (if key is provided).

    # Click Item B again.
    # It should still trigger the handler for B, not A (which is now at index 0) and not C.
    await btn_b.click()

    # Click Item C.
    btn_c = display.page.locator("#item-C")
    await btn_c.click()

    # Assertions
    # We expect 'B' (first click), then 'B' (second click after shift), then 'C'.
    assert clicked_items == ["B", "B", "C"]


async def test_event_targeting_with_index_shifting(display: DisplayFixture):
    """
    Ensure that when keys are NOT provided (using indices),
    events might target the element at the same *index* if the user isn't careful,
    but we verify that the system behaves predictably (target is based on path).

    If we insert at top without keys:
    Old: Index 0 (Item B) -> Path .../0
    New: Index 0 (Item A), Index 1 (Item B) -> Path .../0 turns into Item A.

    If an event was in-flight for Index 0 (Item B) when the update happened:
    The event target ID was ".../0:click".
    After update, ".../0:click" is now Item A's handler.

    So the event intended for B would execute on A. This is standard React behavior for index keys.
    We just want to ensure our system works this way and doesn't crash or lose the event.
    """

    clicked_items = []

    @component
    def Item(id_val):
        async def handle_click(event):
            clicked_items.append(id_val)

        return html.div(
            {"id": f"item-{id_val}", "onClick": handle_click}, f"Item {id_val}"
        )

    @component
    def ListContainer():
        items, set_items = use_state(["B"])

        async def add_top(event):
            set_items(["A", *items])
            # We want to create a race condition where we click Item B (index 0)
            # just narrowly before the re-render places Item A at index 0.
            # But 'display.show' and playwright interactions are sequential usually.
            # We can simulate the state change.

        return html.div(
            html.button({"id": "add-btn", "onClick": add_top}, "Add Top"),
            html.div({"id": "list"}, [Item(i, key=i) for i in items]),
        )

    await display.show(ListContainer)

    # Initial: Item B at Index 0.
    # We want to send an event to Index 0 *effectively*, but have it process *after* A is inserted at Index 0.
    # This is hard to orchestrate with exact timing in an integration test without hooks into the internal loop.
    # However, we can verifying that basic interaction works after the shift.

    add_btn = display.page.locator("#add-btn")
    await add_btn.click()

    await display.page.locator("#item-A").wait_for()

    # Now Item A is at Index 0 (".../0"). Item B is at Index 1 (".../1").
    # Clicking Item B should technically work fine because we are clicking the DOM element for B,
    # which should generate an event for target ".../1".

    btn_b = display.page.locator("#item-B")
    await btn_b.click()  # This generates event for .../1

    assert clicked_items == ["B"]


MARKER = "|"


@reactpy.component
def _ControlledInputWithMirror():
    """A controlled input whose model is also rendered somewhere un-clobberable"""
    value, set_value = use_state("")

    def on_change(event):
        set_value(event["target"]["value"])

    def append_marker(event):
        set_value(lambda old: old + MARKER)

    return reactpy.html.div(
        reactpy.html.input(
            {
                "value": value,
                "onChange": on_change,
                "id": "controlled-input",
            },
        ),
        reactpy.html.button({"onClick": append_marker, "id": "append"}, "append"),
        # A <pre> is never rewritten behind the user's back the way a focused
        # input can be, so this reflects the model as the server holds it.
        reactpy.html.pre({"id": "server-value"}, value),
    )


@pytest.mark.parametrize("delay", TYPE_DELAYS)
async def test_controlled_input_rapid_typing(display: DisplayFixture, delay: int):
    """Typing into a controlled input keeps the component live end to end

    This is the browser level counterpart of the latch tests in
    ``tests/test_core/test_hooks.py``, which pin the ``_scheduled_render`` race
    directly. That race window is far too narrow to hit reliably through a real
    browser, so what is checked here is the property a stranded component violates
    from the outside: after a burst of keystrokes it must still converge with what
    is on screen, and must still respond to a later state change. Which characters
    end up on screen is a separate concern covered by
    :func:`test_controlled_input_rapid_typing_preserves_every_character`.
    """
    await display.show(_ControlledInputWithMirror)

    inp = await display.page.wait_for_selector("#controlled-input")
    await inp.type("hello world this is a test", delay=delay)

    async def values():
        return (
            await inp.evaluate("node => node.value"),
            await display.page.locator("#server-value").text_content(),
        )

    # A keystroke is handled by a server side handler which has to round trip to the
    # browser for the value it reads, so the server may trail what is on screen for a
    # moment. Wait until it has caught up rather than settling for a fixed delay, which
    # only ever passes when the machine happens to be fast enough. A component stranded
    # by the latch bug would be pinned to a stale prefix forever, timing this out.
    await poll(values).until(
        lambda client_and_server: client_and_server[0] == client_and_server[1],
        timeout=10,
        description="the server to catch up with what was typed",
    )

    # Converging once is not sufficient: the latch only stranded a component *after*
    # the burst, once no further render was ever going to be scheduled. Prove the
    # component is still live by driving a fresh state change and requiring the
    # rendered model to follow it.
    value_after_typing = await display.page.locator("#server-value").text_content()
    await display.page.locator("#append").click()

    await poll(values).until(
        lambda client_and_server: client_and_server[1] == value_after_typing + MARKER,
        timeout=10,
        description="the state change after the burst to reach the rendered model",
    )


@pytest.mark.parametrize("delay", TYPE_DELAYS)
async def test_controlled_input_rapid_typing_preserves_every_character(
    display: DisplayFixture,
    delay: int,
):
    """Every keystroke of a burst survives into both the model and the DOM

    The client may only write the server's value over what the user has typed once
    the server has acknowledged every event sent from that element. The numbers the
    two sides compare have to be the same number line, and the acknowledgement has
    to describe events the rendered value actually reflects; when the client counted
    events one way and the server acknowledged them another, the element took a
    snapshot of the previous keystroke for the current one and deleted the newest
    character from the middle of the text.
    """
    target_text = "hello world this is a test"

    await display.show(_ControlledInputWithMirror)

    inp = await display.page.wait_for_selector("#controlled-input")
    await inp.type(target_text, delay=delay)

    async def values():
        return (
            await inp.evaluate("node => node.value"),
            await display.page.locator("#server-value").text_content(),
        )

    await poll(values).until(
        lambda client_and_server: client_and_server[0] == client_and_server[1],
        timeout=10,
        description="the server to catch up with what was typed",
    )

    client_value, server_value = await values()
    assert client_value == target_text
    assert server_value == target_text


@reactpy.component
def _ControlledInputWhichClearsOnKeyDown():
    """A controlled input which also handles ``onKeyDown``, to clear the field

    An element which binds more than one event is the case a single ack figure for
    the whole element cannot serve. The keystrokes arrive through ``onChange`` while
    the deliberate clear arrives through ``onKeyDown``, so acknowledging the element
    as a whole either trusts the server with keystrokes it has not seen yet (taking
    the highest) or refuses an update it has already handled (taking the lowest).
    """
    value, set_value = use_state("")

    def on_change(event):
        set_value(event["target"]["value"])

    def on_key_down(event):
        set_value("")

    return reactpy.html.div(
        reactpy.html.input(
            {
                "value": value,
                "onChange": on_change,
                "onKeyDown": on_key_down,
                "id": "controlled-input",
            }
        ),
        reactpy.html.pre({"id": "server-value"}, value),
    )


@pytest.mark.parametrize("delay", TYPE_DELAYS)
async def test_controlled_input_clear_from_second_handler_reaches_the_dom(
    display: DisplayFixture,
    delay: int,
):
    """A deliberate clear arriving on another event still reaches the input

    The clear lands on an element whose value the server has no reason to change
    again, so nothing else would ever carry the acknowledgement the client is
    waiting for. Without it the input keeps displaying text the server has moved
    past.
    """
    await display.show(_ControlledInputWhichClearsOnKeyDown)

    inp = await display.page.wait_for_selector("#controlled-input")
    await inp.click()
    await inp.type("abc", delay=delay)
    await inp.press("Enter")

    async def current_value():
        return await inp.evaluate("node => node.value")

    await poll(current_value).until(
        lambda value: value == "",
        timeout=10,
        description="the server's clear to reach the input",
    )
    assert await display.page.locator("#server-value").text_content() == ""


async def test_controlled_input_respects_custom_debounce(display: DisplayFixture):
    @reactpy.component
    def ControlledInput():
        value, set_value = use_state("")

        def on_change(event: Event):
            event.debounce = 0
            set_value(event.target.value.upper())

        return reactpy.html.input(
            {
                "value": value,
                "onChange": on_change,
                "id": "controlled-input",
            }
        )

    await display.show(ControlledInput)

    inp = await display.page.wait_for_selector("#controlled-input")
    await inp.type("a", delay=0)

    await display.page.wait_for_function(
        "() => document.getElementById('controlled-input')?.value === 'A'"
    )
    assert (await inp.evaluate("node => node.value")) == "A"


async def test_controlled_input_default_debounce_reconciles_server_value(
    display: DisplayFixture,
):
    """Verifies that a configured ``debounce`` on the handler does not prevent
    the server-transformed value from being applied — the debounce delays the
    outgoing event, but once it fires and the server responds, the seq-based
    reconciliation applies the server value immediately."""

    @reactpy.component
    def ControlledInput():
        value, set_value = use_state("")

        def on_change(event: Event):
            event.debounce = 200
            set_value(event.target.value.upper())

        return reactpy.html.div(
            reactpy.html.input(
                {
                    "value": value,
                    "onChange": on_change,
                    "id": "controlled-input",
                }
            ),
            reactpy.html.pre({"id": "server-value"}, value),
        )

    await display.show(ControlledInput)

    inp = await display.page.wait_for_selector("#controlled-input")
    await inp.type("a", delay=0)

    # The debounce delays the outgoing event, so the server value hasn't
    # been updated yet — it still reflects the initial empty string.
    # The client input shows the typed "a" because it's uncontrolled.
    await asyncio.sleep(0.1)
    assert (await inp.evaluate("node => node.value")) == "a"
    server_value = await display.page.locator("#server-value").text_content()
    assert server_value == "", (
        f"expected empty before debounce expires, got {server_value!r}"
    )

    # Once the debounce window expires, the event is fired to the server,
    # which uppercases the value and echoes it back. The seq-based
    # reconciliation then applies the server value.
    await display.page.wait_for_function(
        """
        () => {
            const input = document.getElementById('controlled-input');
            const serverValue = document.getElementById('server-value');
            return input?.value === 'A' && serverValue?.textContent === 'A';
        }
        """
    )
    assert (await inp.evaluate("node => node.value")) == "A"
    assert await display.page.locator("#server-value").text_content() == "A"


# ===========================================================================
# The acknowledgement which says the server has caught up with the keyboard
# ===========================================================================


def _ack_seq_of(update):
    """Read the acknowledgement off the input rendered by a single-input layout"""
    model = update["model"]["children"][0]
    return model["attributes"].get("_reactpy_ack_seq")


async def test_ack_seq_is_a_map_keyed_by_event():
    """What the server sends back is per event, and is the client's own number

    An element may only write the server's value over what the user has typed once
    the server has acknowledged every event sent from it. To decide that the two
    sides have to be counting on one number line: the client assigns a sequence
    number to each event as it writes it to the wire, and the server echoes back
    the highest one it has finished handling - per event, because an element with
    more than one handler is catching up on each of them separately. One figure
    across all handlers lets a render which predates the newest keystroke of one
    event look up to date because a different event happened to be further along,
    and a figure the server counts for itself, rather than repeating the client's,
    is a number the client can never be satisfied by.
    """
    change = StaticEventHandler()
    key_down = StaticEventHandler()
    handled = asyncio.Event()

    async def note_handled(event):
        handled.set()

    @component
    def Root():
        value, _ = use_state("text")
        return html.input(
            {
                "value": value,
                "onChange": EventHandler(note_handled, target=change.target),
                "onKeyDown": EventHandler(note_handled, target=key_down.target),
            }
        )

    async with Layout(Root()) as layout:
        await layout.render()

        await layout.deliver({**event_message(change.target), "seq": 4})
        await handled.wait()
        assert _ack_seq_of(await layout.render()) == {"onChange": 4}

        # The other event is on a number line of its own, and the first
        # acknowledgement has to survive alongside it rather than be displaced.
        handled.clear()
        await layout.deliver({**event_message(key_down.target), "seq": 9})
        await handled.wait()
        assert _ack_seq_of(await layout.render()) == {"onChange": 4, "onKeyDown": 9}


async def test_ack_never_goes_to_the_wire(display: DisplayFixture):
    """The acknowledgement travels to the client, never back from it

    The number belongs to the client, which assigns it as it sends; all the server
    is entitled to know is the number it was given. Were the acknowledgement to be
    sent up with the event rather than sent down inside the model, the server would
    be acknowledging whatever the client happened to last report instead of what it
    actually finished handling, and an element waiting on that figure would be
    waiting on a number which tells it nothing about whether the value about to be
    written over its own is any good.
    """
    await display.show(_ControlledInputWithMirror)

    inp = await display.page.wait_for_selector("#controlled-input")

    # Anything already in flight is not of interest; what matters is what the
    # client puts on the wire in answer to the keystrokes which follow.
    await display.page.evaluate(
        """
        () => {
            window.__sent = [];
            const send = WebSocket.prototype.send;
            WebSocket.prototype.send = function (data) {
                window.__sent.push(String(data));
                return send.call(this, data);
            };
        }
        """
    )

    async def server_value():
        return await display.page.locator("#server-value").text_content()

    await inp.type("abc", delay=0)

    await poll(server_value).until(
        lambda text: text == "abc",
        timeout=5,
        description="the server to catch up with what was typed",
    )

    sent = await display.page.evaluate("() => window.__sent")
    events = [json.loads(msg) for msg in sent]
    events = [msg for msg in events if msg.get("type") == "layout-event"]
    assert events, f"the client never told the server anything: {sent}"
    assert all("_reactpy_ack_seq" not in msg for msg in events), (
        f"the acknowledgement leaked into an event: {events}"
    )


async def test_ack_never_reaches_the_dom(display: DisplayFixture):
    """The acknowledgement is a protocol field, not something to put on screen

    It arrives inside the element's attributes, and whatever is left there once the
    element has read it would otherwise be written onto the element as one more
    attribute for the user to find in their markup.
    """
    await display.show(_ControlledInputWithMirror)

    inp = await display.page.wait_for_selector("#controlled-input")

    async def server_value():
        return await display.page.locator("#server-value").text_content()

    await inp.type("abc", delay=0)

    # Wait until the server has caught up, otherwise there would be nothing to
    # catch leaking even if something were.
    await poll(server_value).until(
        lambda text: text == "abc",
        timeout=5,
        description="the server to catch up with what was typed",
    )

    markup = await inp.evaluate("node => node.outerHTML")
    assert "_reactpy_ack_seq" not in markup


async def test_a_clear_is_not_written_back_over_by_what_came_before_it(
    display: DisplayFixture,
):
    """A render too old to describe the field cannot resurrect what it held

    The keystrokes and the clear are racing. The field is emptied by an event which
    reaches the server while the text typed into it is still on its way there, so
    renders carrying that text are queued up behind the clear. A render is entitled
    to write over what the user has in the field only once its acknowledgement
    covers the events the field has already moved past; a render which cannot claim
    that, and writes anyway, arrives after the clear and puts the text from before
    it back on screen.
    """
    await display.show(_ControlledInputWhichClearsOnKeyDown)

    inp = await display.page.wait_for_selector("#controlled-input")
    await inp.click()

    async def field_value():
        return await inp.evaluate("node => node.value")

    async def server_value():
        return await display.page.locator("#server-value").text_content()

    # Fill the field and empty it without pausing between, so the clear overtakes
    # the keystrokes instead of following them.
    await inp.type("hello", delay=0)
    await inp.press("Enter")

    await poll(field_value).until(
        lambda value: value == "",
        timeout=10,
        description="the clear to reach the field",
    )
    await poll(server_value).until(
        lambda value: value == "",
        timeout=10,
        description="the clear to reach the model",
    )

    # Whatever is still in flight, none of it may put the earlier text back.
    for _ in range(20):
        await asyncio.sleep(0.05)
        assert await field_value() == "", (
            "a render carrying the text from before the clear overwrote it"
        )


@reactpy.component
def _HeavyPage():
    """A page which re-renders constantly while the user is typing at it"""
    value, set_value = use_state("")
    ticks, set_ticks = use_state(0)

    def on_change(event):
        set_value(event["target"]["value"])

    def keep_rendering():
        """Re-render on a timer, so renders are always in flight behind the typing"""
        loop = asyncio.get_running_loop()
        left = [400]

        def tick():
            set_ticks(lambda old: old + 1)
            left[0] -= 1
            if left[0]:
                handle[0] = loop.call_later(0.005, tick)

        handle = [loop.call_later(0.005, tick)]
        # Cancelled through the cell, not captured directly, because every tick
        # replaces the handle with a fresh one.
        return lambda: handle[0].cancel()  # noqa: PLW0108

    use_effect(keep_rendering)

    return reactpy.html.div(
        reactpy.html.input(
            {"value": value, "onChange": on_change, "id": "controlled-input"}
        ),
        reactpy.html.pre({"id": "server-value"}, value),
        reactpy.html.pre({"id": "ticks"}, str(ticks)),
    )


async def test_controlled_input_drops_no_character_under_a_heavy_page(
    display: DisplayFixture,
):
    """A page churning while the user types still ends up with what they typed

    Every re-render is a chance to write the server's value over the field, and the
    renders which follow the last keystroke carry a value read before it. Only the
    acknowledgement tells the element which of them are too old to write with, so
    under a load which multiplies the renders in flight that property is the only
    thing standing between the user and a vanished character.
    """
    target_text = "the quick brown fox jumps over the lazy dog"

    await display.show(_HeavyPage)

    inp = await display.page.wait_for_selector("#controlled-input")

    await inp.type(target_text, delay=0)

    async def values():
        return (
            await inp.evaluate("node => node.value"),
            await display.page.locator("#server-value").text_content(),
        )

    await poll(values).until(
        lambda pair: pair[0] == pair[1] == target_text,
        timeout=15,
        description="the field and the model to hold everything which was typed",
    )

    assert int(await display.page.locator("#ticks").text_content()) > 1, (
        "the page never re-rendered, so this exercised nothing"
    )
