import pytest

import idom

from tests.general_utils import assert_unordered_equal

from .utils import HookCatcher


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


async def test_set_state_callback_identity_is_preserved():
    saved_set_state_hooks = []

    @idom.element
    async def SimpleStatefulElement():
        index, set_index = idom.hooks.use_state(0)
        saved_set_state_hooks.append(set_index)
        set_index(index + 1)
        return idom.html.div(index)

    sse = SimpleStatefulElement()

    async with idom.Layout(sse) as layout:
        await layout.render()
        await layout.render()
        await layout.render()
        await layout.render()

    first_hook = saved_set_state_hooks[0]
    for h in saved_set_state_hooks[1:]:
        assert first_hook is h


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


def test_set_state_with_reducer_instead_of_value(driver, display):
    def increment(count):
        return count + 1

    @idom.element
    async def Counter():
        count, set_count = idom.hooks.use_state(0)
        return idom.html.button(
            {
                "id": "counter",
                "onClick": lambda event: set_count(increment),
            },
            f"Count: {count}",
        )

    display(Counter)

    client_counter = driver.find_element_by_id("counter")

    for i in range(3):
        assert client_counter.get_attribute("innerHTML") == f"Count: {i}"
        client_counter.click()


def test_set_state_checks_identity_not_equality(driver, display, driver_wait):
    r_1 = idom.Ref("value")
    r_2 = idom.Ref("value")

    # refs are equal but not identical
    assert r_1 == r_2
    assert r_1 is not r_2

    render_count = idom.Ref(0)
    event_count = idom.Ref(0)

    def event_count_tracker(function):
        def tracker(*args, **kwargs):
            event_count.current += 1
            return function(*args, **kwargs)

        return tracker

    @idom.element
    async def TestElement():
        state, set_state = idom.hooks.use_state(r_1)

        render_count.current += 1
        return idom.html.div(
            idom.html.button(
                {
                    "id": "r_1",
                    "onClick": event_count_tracker(lambda event: set_state(r_1)),
                },
                "r_1",
            ),
            idom.html.button(
                {
                    "id": "r_2",
                    "onClick": event_count_tracker(lambda event: set_state(r_2)),
                },
                "r_2",
            ),
            f"Last state: {'r_1' if state is r_1 else 'r_2'}",
        )

    display(TestElement)

    client_r_1_button = driver.find_element_by_id("r_1")
    client_r_2_button = driver.find_element_by_id("r_2")

    assert render_count.current == 1
    assert event_count.current == 0

    client_r_1_button.click()

    driver_wait.until(lambda d: event_count.current == 1)
    assert render_count.current == 1

    client_r_2_button.click()

    driver_wait.until(lambda d: event_count.current == 2)
    assert render_count.current == 2

    client_r_2_button.click()

    driver_wait.until(lambda d: event_count.current == 3)
    assert render_count.current == 2


def test_simple_input_with_use_state(driver, display):
    message_ref = idom.Ref(None)

    @idom.element
    async def Input(message=None):
        message, set_message = idom.hooks.use_state(message)
        message_ref.current = message

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


async def test_use_effect_callback_occurs_after_full_render_is_complete():
    effect_triggered = idom.Ref(False)
    effect_triggers_after_final_render = idom.Ref(None)

    @idom.element
    async def OuterElement():
        return idom.html.div(
            ElementWithEffect(),
            CheckNoEffectYet(),
        )

    @idom.element
    async def ElementWithEffect():
        @idom.hooks.use_effect
        def effect():
            effect_triggered.current = True

        return idom.html.div()

    @idom.element
    async def CheckNoEffectYet():
        effect_triggers_after_final_render.current = not effect_triggered.current
        return idom.html.div()

    async with idom.Layout(OuterElement()) as layout:
        await layout.render()

    assert effect_triggered.current
    assert effect_triggers_after_final_render.current is not None
    assert effect_triggers_after_final_render.current


async def test_use_effect_cleanup_occurs_on_will_render():
    element_hook = HookCatcher()
    cleanup_triggered = idom.Ref(False)
    cleanup_triggered_before_next_render = idom.Ref(False)

    @idom.element
    @element_hook.capture
    async def ElementWithEffect():
        if cleanup_triggered.current:
            cleanup_triggered_before_next_render.current = True

        @idom.hooks.use_effect
        def effect():
            def cleanup():
                cleanup_triggered.current = True

            return cleanup

        return idom.html.div()

    async with idom.Layout(ElementWithEffect()) as layout:
        await layout.render()

        assert not cleanup_triggered.current

        element_hook.schedule_render()
        await layout.render()

        assert cleanup_triggered.current
        assert cleanup_triggered_before_next_render.current


async def test_use_effect_cleanup_occurs_on_will_unmount():
    outer_element_hook = HookCatcher()
    cleanup_triggered = idom.Ref(False)
    cleanup_triggered_before_next_render = idom.Ref(False)

    @idom.element
    @outer_element_hook.capture
    async def OuterElement():
        if cleanup_triggered.current:
            cleanup_triggered_before_next_render.current = True
        return ElementWithEffect()

    @idom.element
    async def ElementWithEffect():
        @idom.hooks.use_effect
        def effect():
            def cleanup():
                cleanup_triggered.current = True

            return cleanup

        return idom.html.div()

    async with idom.Layout(OuterElement()) as layout:
        await layout.render()

        assert not cleanup_triggered.current

        outer_element_hook.schedule_render()
        await layout.render()

        assert cleanup_triggered.current
        assert cleanup_triggered_before_next_render.current


async def test_use_effect_memoization():
    element_hook = HookCatcher()
    set_state_callback = idom.Ref(None)
    effect_run_count = idom.Ref(0)

    first_value = 1
    second_value = 2

    @idom.element
    @element_hook.capture
    async def ElementWithMemoizedEffect():
        state, set_state_callback.current = idom.hooks.use_state(first_value)

        @idom.hooks.use_effect(args=[state])
        def effect():
            effect_run_count.current += 1

        return idom.html.div()

    async with idom.Layout(ElementWithMemoizedEffect()) as layout:
        await layout.render()

        assert effect_run_count.current == 1

        element_hook.schedule_render()
        await layout.render()

        assert effect_run_count.current == 1

        set_state_callback.current(second_value)
        await layout.render()

        assert effect_run_count.current == 2

        element_hook.schedule_render()
        await layout.render()

        assert effect_run_count.current == 2


async def test_use_reducer():
    saved_count = idom.Ref(None)
    saved_dispatch = idom.Ref(None)

    def reducer(count, action):
        if action == "increment":
            return count + 1
        elif action == "decrement":
            return count - 1
        else:
            raise ValueError(f"Unknown action '{action}'")

    @idom.element
    async def Counter(initial_count):
        saved_count.current, saved_dispatch.current = idom.hooks.use_reducer(
            reducer, initial_count
        )
        return idom.html.div()

    async with idom.Layout(Counter(0)) as layout:
        await layout.render()

        assert saved_count.current == 0

        saved_dispatch.current("increment")
        await layout.render()

        assert saved_count.current == 1

        saved_dispatch.current("decrement")
        await layout.render()

        assert saved_count.current == 0


async def test_use_reducer_dispatch_callback_identity_is_preserved():
    saved_dispatchers = []

    def reducer(count, action):
        if action == "increment":
            return count + 1
        else:
            raise ValueError(f"Unknown action '{action}'")

    @idom.element
    async def ElementWithUseReduce():
        saved_dispatchers.append(idom.hooks.use_reducer(reducer, 0)[1])
        return idom.html.div()

    async with idom.Layout(ElementWithUseReduce()) as layout:
        for _ in range(3):
            await layout.render()
            saved_dispatchers[-1]("increment")

    first_dispatch = saved_dispatchers[0]
    for d in saved_dispatchers[1:]:
        assert first_dispatch is d


def test_use_callback_identity():
    assert False


def test_use_callback_memoization():
    assert False


def test_use_memo():
    assert False


def test_use_memo_always_runs_if_args_are_none():
    assert False


def test_use_memo_never_runs_if_args_args_empty_list():
    assert False


def test_use_memo_decorator_and_non_decorator_usage():
    assert False


def test_use_ref():
    assert False
