import gc
import time
from weakref import ref

import pytest

import idom


def test_cannot_access_current_hook_dispatch_if_none_active():
    with pytest.raises(RuntimeError, match="No hook dispatcher is active"):
        idom.hooks.current_hook_dispatcher()


async def test_simple_stateful_element():
    @idom.element
    async def simple_stateful_element():
        index, set_index = idom.hooks.use_state(0)
        set_index(index + 1)
        return idom.html.div(index)

    ssd = simple_stateful_element()

    async with idom.Layout(ssd) as layout:
        assert (await layout.render()).new[ssd.id] == {
            "tagName": "div",
            "children": [{"data": "0", "type": "str"}],
        }
        assert (await layout.render()).new[ssd.id] == {
            "tagName": "div",
            "children": [{"data": "1", "type": "str"}],
        }
        assert (await layout.render()).new[ssd.id] == {
            "tagName": "div",
            "children": [{"data": "2", "type": "str"}],
        }


def test_simple_input(driver, display):
    message_var = idom.Var(None)

    @idom.element
    async def Input(message=None):
        message, set_message = idom.hooks.use_state(message)
        message_var.set(message)

        async def on_change(event):
            if event["value"] == "this is a test":
                set_message(event["value"])

        if message is None:
            return idom.html.input({"id": "input", "onChange": on_change})
        else:
            return idom.html.p({"id": "complete"}, ["Complete"])

    display(Input)

    button = driver.find_element_by_id("input")
    button.send_keys("this is a test")
    driver.find_element_by_id("complete")

    assert message_var.get() == "this is a test"


def test_rate_limit(driver, display):
    @idom.element
    async def Counter():
        count, set_count = idom.hooks.use_state(0)

        await idom.hooks.use_frame_rate(0.1)

        if count < 5:
            set_count(count + 1)

        return idom.html.p({"id": f"counter-{count}"}, [f"Count: {count}"])

    start = time.time()
    display(Counter)
    driver.find_element_by_id("counter-5")
    stop = time.time()

    elapsed = stop - start
    assert elapsed > 0.5


def test_use_memo(display, driver, driver_wait):
    trigger_count = 0

    def function_to_memoize(some_value):
        nonlocal trigger_count
        trigger_count += 1
        return trigger_count

    @idom.element
    async def ComponentWithMemo():
        location, set_location = idom.hooks.use_state("left")
        count = idom.hooks.use_memo(function_to_memoize, location)

        async def on_left_button_click(event):
            set_location("left")

        async def on_right_button_click(event):
            set_location("right")

        return idom.html.div(
            idom.html.button(
                {"onClick": on_left_button_click, "id": "left-button"}, "left button"
            ),
            idom.html.button(
                {"onClick": on_right_button_click, "id": "right-button"}, "right button"
            ),
            f"Memo trigger count: {count}",
        )

    display(ComponentWithMemo)  # initial render triggers: yes

    left_client_button = driver.find_element_by_id("left-button")
    right_client_button = driver.find_element_by_id("right-button")

    right_client_button.click()  # trigger: yes
    right_client_button.click()  # trigger: no
    right_client_button.click()  # trigger: no
    left_client_button.click()  # trigger: yes
    left_client_button.click()  # trigger: no
    right_client_button.click()  # trigger: yes

    driver_wait.until(lambda drv: trigger_count == 4)


def test_use_lru_cache(display, driver, driver_wait):
    calls = []

    def function_to_memoize(some_value):
        calls.append(some_value)
        return some_value

    @idom.element
    async def ComponentWithMemo():
        location, set_location = idom.hooks.use_state("left")
        memoized_func = idom.hooks.use_lru_cache(function_to_memoize, maxsize=2)
        last_memoized_location = memoized_func(location)

        async def on_left_button_click(event):
            set_location("left")

        async def on_center_button_click(event):
            set_location("center")

        async def on_right_button_click(event):
            set_location("right")

        return idom.html.div(
            idom.html.button(
                {"onClick": on_left_button_click, "id": "left-button"}, "left button"
            ),
            idom.html.button(
                {"onClick": on_center_button_click, "id": "center-button"},
                "center button",
            ),
            idom.html.button(
                {"onClick": on_right_button_click, "id": "right-button"}, "right button"
            ),
            f"Last triggered on click: {last_memoized_location}",
        )

    display(ComponentWithMemo)  # cache state (triggers): [left, None]

    left_client_button = driver.find_element_by_id("left-button")
    center_client_button = driver.find_element_by_id("center-button")
    right_client_button = driver.find_element_by_id("right-button")

    center_client_button.click()  # cache state (triggers): [center, left]
    left_client_button.click()  # cache state: [left, center]
    right_client_button.click()  # cache state (triggers): [right, left]
    center_client_button.click()  # cache state (triggers): [center, right]
    center_client_button.click()  # cache state: [center, right]

    driver_wait.until(lambda drv: calls == ["left", "center", "right", "center"])


def test_cannot_create_update_callback_after_element_is_garbage_collected():
    @idom.element
    async def SomeElement():
        ...

    element = SomeElement()

    hook = idom.hooks.Hook(idom.Layout(element), ref(element))

    # cause garbage collection
    del hook._layout
    del element
    gc.collect()

    with pytest.raises(RuntimeError, match=r"Element for hook .* no longer exists"):
        hook.create_update_callback()


def test_hook_dispatcher_cannot_dispatch_hook_when_not_rendering():
    @idom.element
    async def SomeElement():
        ...

    hook_dispatcher = idom.hooks.HookDispatcher(idom.Layout(SomeElement()))

    with pytest.raises(
        RuntimeError, match=r"Hook dispatcher .* is not rendering any element"
    ):
        hook_dispatcher.dispatch_hook()
