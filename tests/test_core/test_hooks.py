import re
import asyncio

import pytest

import idom

from tests.general_utils import assert_same_items, HookCatcher


async def test_must_be_rendering_in_layout_to_use_hooks():
    @idom.element
    def SimpleElementWithHook():
        idom.hooks.use_state(None)
        return idom.html.div()

    with pytest.raises(RuntimeError, match="No life cycle hook is active"):
        await SimpleElementWithHook().render()

    async with idom.Layout(SimpleElementWithHook()) as layout:
        await layout.render()


async def test_simple_stateful_element():
    @idom.element
    def SimpleStatefulElement():
        index, set_index = idom.hooks.use_state(0)
        set_index(index + 1)
        return idom.html.div(index)

    sse = SimpleStatefulElement()

    async with idom.Layout(sse) as layout:
        patch_1 = await layout.render()
        assert patch_1.path == ""
        assert_same_items(
            patch_1.changes,
            [
                {"op": "add", "path": "/children", "value": ["0"]},
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
    def SimpleStatefulElement():
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
    def Outer():
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
    def Inner():
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
    def Counter():
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
    def TestElement():
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
    def Input(message=None):
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
    def OuterElement():
        return idom.html.div(
            ElementWithEffect(),
            CheckNoEffectYet(),
        )

    @idom.element
    def ElementWithEffect():
        @idom.hooks.use_effect
        def effect():
            effect_triggered.current = True

        return idom.html.div()

    @idom.element
    def CheckNoEffectYet():
        effect_triggers_after_final_render.current = not effect_triggered.current
        return idom.html.div()

    async with idom.Layout(OuterElement()) as layout:
        await layout.render()

    assert effect_triggered.current
    assert effect_triggers_after_final_render.current is not None
    assert effect_triggers_after_final_render.current


async def test_use_effect_cleanup_occurs_before_next_effect():
    element_hook = HookCatcher()
    cleanup_triggered = idom.Ref(False)
    cleanup_triggered_before_next_effect = idom.Ref(False)

    @idom.element
    @element_hook.capture
    def ElementWithEffect():
        @idom.hooks.use_effect
        def effect():
            if cleanup_triggered.current:
                cleanup_triggered_before_next_effect.current = True

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
        assert cleanup_triggered_before_next_effect.current


async def test_use_effect_cleanup_occurs_on_will_unmount():
    outer_element_hook = HookCatcher()
    cleanup_triggered = idom.Ref(False)
    cleanup_triggered_before_next_render = idom.Ref(False)

    @idom.element
    @outer_element_hook.capture
    def OuterElement():
        if cleanup_triggered.current:
            cleanup_triggered_before_next_render.current = True
        return ElementWithEffect()

    @idom.element
    def ElementWithEffect():
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


async def test_memoized_effect_on_recreated_if_args_change():
    element_hook = HookCatcher()
    set_state_callback = idom.Ref(None)
    effect_run_count = idom.Ref(0)

    first_value = 1
    second_value = 2

    @idom.element
    @element_hook.capture
    def ElementWithMemoizedEffect():
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


async def test_memoized_effect_cleanup_only_triggered_before_new_effect():
    element_hook = HookCatcher()
    set_state_callback = idom.Ref(None)
    cleanup_trigger_count = idom.Ref(0)

    first_value = 1
    second_value = 2

    @idom.element
    @element_hook.capture
    def ElementWithEffect():
        state, set_state_callback.current = idom.hooks.use_state(first_value)

        @idom.hooks.use_effect(args=[state])
        def effect():
            def cleanup():
                cleanup_trigger_count.current += 1

            return cleanup

        return idom.html.div()

    async with idom.Layout(ElementWithEffect()) as layout:
        await layout.render()

        assert cleanup_trigger_count.current == 0

        element_hook.schedule_render()
        await layout.render()

        assert cleanup_trigger_count.current == 0

        set_state_callback.current(second_value)
        await layout.render()

        assert cleanup_trigger_count.current == 1


async def test_use_async_effect():
    effect_ran = asyncio.Event()

    @idom.element
    def ElementWithAsyncEffect():
        @idom.hooks.use_effect
        async def effect():
            effect_ran.set()

        return idom.html.div()

    async with idom.Layout(ElementWithAsyncEffect()) as layout:
        await layout.render()
        await effect_ran.wait()


async def test_use_async_effect_cleanup():
    element_hook = HookCatcher()
    effect_ran = asyncio.Event()
    cleanup_ran = asyncio.Event()

    @idom.element
    @element_hook.capture
    def ElementWithAsyncEffect():
        @idom.hooks.use_effect
        async def effect():
            effect_ran.set()
            return cleanup_ran.set

        return idom.html.div()

    async with idom.Layout(ElementWithAsyncEffect()) as layout:
        await layout.render()

        await effect_ran.wait()
        element_hook.schedule_render()

        await layout.render()

    await asyncio.wait_for(cleanup_ran.wait(), 1)


async def test_use_async_effect_cancel(caplog):
    element_hook = HookCatcher()
    effect_ran = asyncio.Event()
    effect_was_cancelled = asyncio.Event()

    event_that_never_occurs = asyncio.Event()

    @idom.element
    @element_hook.capture
    def ElementWithLongWaitingEffect():
        @idom.hooks.use_effect
        async def effect():
            effect_ran.set()
            try:
                await event_that_never_occurs.wait()
            except asyncio.CancelledError:
                effect_was_cancelled.set()
                raise

        return idom.html.div()

    async with idom.Layout(ElementWithLongWaitingEffect()) as layout:
        await layout.render()

        await effect_ran.wait()
        element_hook.schedule_render()

        await layout.render()

    await asyncio.wait_for(effect_was_cancelled.wait(), 1)

    # So I know we said the event never occurs but... to ensure the effect's future is
    # cancelled before the test is cleaned up we need to set the event. This is because
    # the cancellation doesn't propogate before the test is resolved which causes
    # delayed log messages that impact other tests.
    event_that_never_occurs.set()


async def test_error_in_effect_is_gracefully_handled(caplog):
    @idom.element
    def ElementWithEffect():
        @idom.hooks.use_effect
        def bad_effect():
            raise ValueError("Something went wong :(")

        return idom.html.div()

    async with idom.Layout(ElementWithEffect()) as layout:
        await layout.render()  # no error

    first_log_line = next(iter(caplog.records)).msg.split("\n", 1)[0]
    assert re.match("Post-render effect .*? failed for .*?", first_log_line)


async def test_error_in_effect_cleanup_is_gracefully_handled(caplog):
    caplog.clear()
    element_hook = HookCatcher()

    @idom.element
    @element_hook.capture
    def ElementWithEffect():
        @idom.hooks.use_effect
        def ok_effect():
            def bad_cleanup():
                raise ValueError("Something went wong :(")

            return bad_cleanup

        return idom.html.div()

    async with idom.Layout(ElementWithEffect()) as layout:
        await layout.render()
        element_hook.schedule_render()
        await layout.render()  # no error

    first_log_line = next(iter(caplog.records)).msg.split("\n", 1)[0]
    assert re.match("Post-render effect .*? failed for .*?", first_log_line)


async def test_error_in_effect_pre_unmount_cleanup_is_gracefully_handled(caplog):
    outer_element_hook = HookCatcher()

    @idom.element
    @outer_element_hook.capture
    def OuterElement():
        return ElementWithEffect()

    @idom.element
    def ElementWithEffect():
        @idom.hooks.use_effect
        def ok_effect():
            def bad_cleanup():
                raise ValueError("Something went wong :(")

            return bad_cleanup

        return idom.html.div()

    async with idom.Layout(OuterElement()) as layout:
        await layout.render()
        outer_element_hook.schedule_render()
        await layout.render()  # no error

    first_log_line = next(iter(caplog.records)).msg.split("\n", 1)[0]
    assert re.match("Pre-unmount effect .*? failed for .*?", first_log_line)


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
    def Counter(initial_count):
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
    def ElementWithUseReduce():
        saved_dispatchers.append(idom.hooks.use_reducer(reducer, 0)[1])
        return idom.html.div()

    async with idom.Layout(ElementWithUseReduce()) as layout:
        for _ in range(3):
            await layout.render()
            saved_dispatchers[-1]("increment")

    first_dispatch = saved_dispatchers[0]
    for d in saved_dispatchers[1:]:
        assert first_dispatch is d


async def test_use_callback_identity():
    element_hook = HookCatcher()
    used_callbacks = []

    @idom.element
    @element_hook.capture
    def ElementWithRef():
        used_callbacks.append(idom.hooks.use_callback(lambda: None))
        return idom.html.div()

    async with idom.Layout(ElementWithRef()) as layout:
        await layout.render()
        element_hook.schedule_render()
        await layout.render()

    assert used_callbacks[0] is used_callbacks[1]
    assert len(used_callbacks) == 2


async def test_use_callback_memoization():
    element_hook = HookCatcher()
    set_state_hook = idom.Ref(None)
    used_callbacks = []

    @idom.element
    @element_hook.capture
    def ElementWithRef():
        state, set_state_hook.current = idom.hooks.use_state(0)

        @idom.hooks.use_callback(args=[state])  # use the deco form for coverage
        def cb():
            return None

        used_callbacks.append(cb)
        return idom.html.div()

    async with idom.Layout(ElementWithRef()) as layout:
        await layout.render()
        set_state_hook.current(1)
        await layout.render()
        element_hook.schedule_render()
        await layout.render()

    assert used_callbacks[0] is not used_callbacks[1]
    assert used_callbacks[1] is used_callbacks[2]
    assert len(used_callbacks) == 3


async def test_use_memo():
    element_hook = HookCatcher()
    set_state_hook = idom.Ref(None)
    used_values = []

    @idom.element
    @element_hook.capture
    def ElementWithMemo():
        state, set_state_hook.current = idom.hooks.use_state(0)
        value = idom.hooks.use_memo(
            lambda: idom.Ref(state),  # use a Ref here just to ensure it's a unique obj
            [state],
        )
        used_values.append(value)
        return idom.html.div()

    async with idom.Layout(ElementWithMemo()) as layout:
        await layout.render()
        set_state_hook.current(1)
        await layout.render()
        element_hook.schedule_render()
        await layout.render()

    assert used_values[0] is not used_values[1]
    assert used_values[1] is used_values[2]
    assert len(used_values) == 3


async def test_use_memo_always_runs_if_args_are_none():
    element_hook = HookCatcher()
    used_values = []

    iter_values = iter([1, 2, 3])

    @idom.element
    @element_hook.capture
    def ElementWithMemo():
        value = idom.hooks.use_memo(lambda: next(iter_values))
        used_values.append(value)
        return idom.html.div()

    async with idom.Layout(ElementWithMemo()) as layout:
        await layout.render()
        element_hook.schedule_render()
        await layout.render()
        element_hook.schedule_render()
        await layout.render()

    assert used_values == [1, 2, 3]


async def test_use_memo_with_stored_args_is_empty_tuple_after_args_are_none():
    element_hook = HookCatcher()
    used_values = []

    iter_values = iter([1, 2, 3])
    args_used_in_memo = idom.Ref(())

    @idom.element
    @element_hook.capture
    def ElementWithMemo():
        value = idom.hooks.use_memo(
            lambda: next(iter_values), args_used_in_memo.current
        )
        used_values.append(value)
        return idom.html.div()

    async with idom.Layout(ElementWithMemo()) as layout:
        await layout.render()
        element_hook.schedule_render()
        args_used_in_memo.current = None
        await layout.render()
        element_hook.schedule_render()
        args_used_in_memo.current = ()
        await layout.render()

    assert used_values == [1, 2, 2]


async def test_use_memo_never_runs_if_args_args_empty_list():
    element_hook = HookCatcher()
    used_values = []

    iter_values = iter([1, 2, 3])

    @idom.element
    @element_hook.capture
    def ElementWithMemo():
        value = idom.hooks.use_memo(lambda: next(iter_values), ())
        used_values.append(value)
        return idom.html.div()

    async with idom.Layout(ElementWithMemo()) as layout:
        await layout.render()
        element_hook.schedule_render()
        await layout.render()
        element_hook.schedule_render()
        await layout.render()

    assert used_values == [1, 1, 1]


async def test_use_ref():
    element_hook = HookCatcher()
    used_refs = []

    @idom.element
    @element_hook.capture
    def ElementWithRef():
        used_refs.append(idom.hooks.use_ref(1))
        return idom.html.div()

    async with idom.Layout(ElementWithRef()) as layout:
        await layout.render()
        element_hook.schedule_render()
        await layout.render()

    assert used_refs[0] is used_refs[1]
    assert len(used_refs) == 2
