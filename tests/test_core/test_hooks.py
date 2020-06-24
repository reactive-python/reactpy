import time

import pytest

import idom


def test_cannot_access_current_hook_dispatch_if_none_active():
    with pytest.raises(RuntimeError, "No hook dispatcher is active"):
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

        await idom.hooks.use_rate_limit(0.1)

        if count < 5:
            set_count(count + 1)

        return idom.html.p({"id": f"counter-{count}"}, [f"Count: {count}"])

    start = time.time()
    display(Counter)
    driver.find_element_by_id("counter-5")
    stop = time.time()

    elapsed = stop - start
    assert elapsed > 0.5
