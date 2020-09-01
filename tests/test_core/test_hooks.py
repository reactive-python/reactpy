import pytest

import idom

from tests.general_utils import assert_unordered_equal


async def test_must_be_rendering_in_layout_to_use_hooks():
    @idom.element
    async def SimpleElementWithHook():
        idom.hooks.use_state(None)
        return idom.html.div()

    with pytest.raises(RuntimeError, match="No life cycle hook is active"):
        await SimpleElementWithHook().render()

    async with idom.Layout(SimpleElementWithHook()) as layout:
        await layout.render()


async def test_simple_stateful_element():
    @idom.element
    async def SimpleStatefulElement():
        index, set_index = idom.hooks.use_state(0)
        set_index(index + 1)
        return idom.html.div(index)

    sse = SimpleStatefulElement()

    async with idom.Layout(sse) as layout:
        patch_1 = await layout.render()
        assert patch_1.path == ""
        assert_unordered_equal(
            patch_1.changes,
            [
                {"op": "add", "path": "/children", "value": ["0"]},
                {"op": "add", "path": "/eventHandlers", "value": {}},
                {"op": "add", "path": "/tagName", "value": "div"},
            ],
        )

        patch_2 = await layout.render()
        assert patch_2.path == ""
        assert patch_2.changes == [
            {"op": "replace", "path": "/children/0", "value": "1"}
        ]

        patch_3 = await layout.render()
        assert patch_3.path == ""
        assert patch_3.changes == [
            {"op": "replace", "path": "/children/0", "value": "2"}
        ]


def test_use_state_with_constructor(driver, display, driver_wait):
    constructor_call_count = idom.Ref(0)

    def make_default():
        constructor_call_count.current += 1
        return 0

    @idom.element
    async def Outer():
        hook = idom.hooks.current_hook()

        async def on_click(event):
            hook.schedule_render()

        return idom.html.div(
            idom.html.button(
                {"onClick": on_click, "id": "outer"}, "update outer (rerun constructor)"
            ),
            Inner(),
        )

    @idom.element
    async def Inner():
        count, set_count = idom.hooks.use_state(make_default)

        async def on_click(event):
            set_count(count + 1)

        return idom.html.div(
            idom.html.button(
                {"onClick": on_click, "id": "inner"},
                "update inner with state constructor",
            ),
            idom.html.p({"id": "count-view"}, count),
        )

    display(Outer)

    outer = driver.find_element_by_id("outer")
    inner = driver.find_element_by_id("inner")
    count = driver.find_element_by_id("count-view")

    assert constructor_call_count.current == 1
    assert count.get_attribute("innerHTML") == "0"

    inner.click()

    assert constructor_call_count.current == 1
    assert count.get_attribute("innerHTML") == "1"

    outer.click()

    assert constructor_call_count.current == 2
    assert count.get_attribute("innerHTML") == "0"

    inner.click()

    assert constructor_call_count.current == 2
    assert count.get_attribute("innerHTML") == "1"


def test_simple_input(driver, display):
    message_ref = idom.Ref(None)

    @idom.element
    async def Input(message=None):
        message, set_message = idom.hooks.use_state(message)
        message_ref.set(message)

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

    assert message_ref.current == "this is a test"


def test_use_memo(display, driver, driver_wait):
    trigger_count = 0

    @idom.element
    async def ComponentWithMemo():
        location, set_location = idom.hooks.use_state("left")

        @idom.hooks.use_memo(args=location)
        def count():
            nonlocal trigger_count
            trigger_count += 1
            return trigger_count

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
