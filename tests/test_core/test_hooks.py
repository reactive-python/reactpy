import asyncio
import re

import pytest

import idom
from idom.core.dispatcher import render_json_patch
from idom.core.hooks import LifeCycleHook
from idom.testing import HookCatcher, assert_idom_logged
from tests.general_utils import assert_same_items


async def test_must_be_rendering_in_layout_to_use_hooks():
    @idom.component
    def SimpleComponentWithHook():
        idom.hooks.use_state(None)
        return idom.html.div()

    with pytest.raises(RuntimeError, match="No life cycle hook is active"):
        await SimpleComponentWithHook().render()

    with idom.Layout(SimpleComponentWithHook()) as layout:
        await layout.render()


async def test_simple_stateful_component():
    @idom.component
    def SimpleStatefulComponent():
        index, set_index = idom.hooks.use_state(0)
        set_index(index + 1)
        return idom.html.div(index)

    sse = SimpleStatefulComponent()

    with idom.Layout(sse) as layout:
        patch_1 = await render_json_patch(layout)
        assert patch_1.path == ""
        assert_same_items(
            patch_1.changes,
            [
                {"op": "add", "path": "/children", "value": ["0"]},
                {"op": "add", "path": "/tagName", "value": "div"},
            ],
        )

        patch_2 = await render_json_patch(layout)
        assert patch_2.path == ""
        assert patch_2.changes == [
            {"op": "replace", "path": "/children/0", "value": "1"}
        ]

        patch_3 = await render_json_patch(layout)
        assert patch_3.path == ""
        assert patch_3.changes == [
            {"op": "replace", "path": "/children/0", "value": "2"}
        ]


async def test_set_state_callback_identity_is_preserved():
    saved_set_state_hooks = []

    @idom.component
    def SimpleStatefulComponent():
        index, set_index = idom.hooks.use_state(0)
        saved_set_state_hooks.append(set_index)
        set_index(index + 1)
        return idom.html.div(index)

    sse = SimpleStatefulComponent()

    with idom.Layout(sse) as layout:
        await layout.render()
        await layout.render()
        await layout.render()
        await layout.render()

    first_hook = saved_set_state_hooks[0]
    for h in saved_set_state_hooks[1:]:
        assert first_hook is h


async def test_use_state_with_constructor():
    constructor_call_count = idom.Ref(0)

    set_outer_state = idom.Ref()
    set_inner_key = idom.Ref()
    set_inner_state = idom.Ref()

    def make_default():
        constructor_call_count.current += 1
        return 0

    @idom.component
    def Outer():
        state, set_outer_state.current = idom.use_state(0)
        inner_key, set_inner_key.current = idom.use_state("first")
        return idom.html.div(state, Inner(key=inner_key))

    @idom.component
    def Inner():
        state, set_inner_state.current = idom.use_state(make_default)
        return idom.html.div(state)

    with idom.Layout(Outer()) as layout:
        await layout.render()

        assert constructor_call_count.current == 1

        set_outer_state.current(1)
        await layout.render()

        assert constructor_call_count.current == 1

        set_inner_state.current(1)
        await layout.render()

        assert constructor_call_count.current == 1

        set_inner_key.current("second")
        await layout.render()

        assert constructor_call_count.current == 2


async def test_set_state_with_reducer_instead_of_value():
    count = idom.Ref()
    set_count = idom.Ref()

    def increment(count):
        return count + 1

    @idom.component
    def Counter():
        count.current, set_count.current = idom.hooks.use_state(0)
        return idom.html.div(count.current)

    with idom.Layout(Counter()) as layout:
        await layout.render()

        for i in range(4):
            assert count.current == i
            set_count.current(increment)
            await layout.render()


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

    @idom.component
    def TestComponent():
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

    display(TestComponent)

    client_r_1_button = driver.find_element("id", "r_1")
    client_r_2_button = driver.find_element("id", "r_2")

    assert render_count.current == 1
    assert event_count.current == 0

    client_r_1_button.click()

    driver_wait.until(lambda d: event_count.current == 1)
    driver_wait.until(lambda d: render_count.current == 1)

    client_r_2_button.click()

    driver_wait.until(lambda d: event_count.current == 2)
    driver_wait.until(lambda d: render_count.current == 2)

    client_r_2_button.click()

    driver_wait.until(lambda d: event_count.current == 3)
    driver_wait.until(lambda d: render_count.current == 2)


def test_simple_input_with_use_state(driver, display):
    message_ref = idom.Ref(None)

    @idom.component
    def Input(message=None):
        message, set_message = idom.hooks.use_state(message)
        message_ref.current = message

        async def on_change(event):
            if event["target"]["value"] == "this is a test":
                set_message(event["target"]["value"])

        if message is None:
            return idom.html.input({"id": "input", "onChange": on_change})
        else:
            return idom.html.p({"id": "complete"}, ["Complete"])

    display(Input)

    button = driver.find_element("id", "input")
    button.send_keys("this is a test")
    driver.find_element("id", "complete")

    assert message_ref.current == "this is a test"


def test_double_set_state(driver, driver_wait, display):
    @idom.component
    def SomeComponent():
        state_1, set_state_1 = idom.hooks.use_state(0)
        state_2, set_state_2 = idom.hooks.use_state(0)

        def double_set_state(event):
            set_state_1(state_1 + 1)
            set_state_2(state_2 + 1)

        return idom.html.div(
            idom.html.div({"id": "first", "value": state_1}, f"value is: {state_1}"),
            idom.html.div({"id": "second", "value": state_2}, f"value is: {state_2}"),
            idom.html.button({"id": "button", "onClick": double_set_state}, "click me"),
        )

    display(SomeComponent)

    button = driver.find_element("id", "button")
    first = driver.find_element("id", "first")
    second = driver.find_element("id", "second")

    assert first.get_attribute("value") == "0"
    assert second.get_attribute("value") == "0"

    button.click()

    assert driver_wait.until(lambda _: first.get_attribute("value") == "1")
    assert driver_wait.until(lambda _: second.get_attribute("value") == "1")

    button.click()

    assert driver_wait.until(lambda _: first.get_attribute("value") == "2")
    assert driver_wait.until(lambda _: second.get_attribute("value") == "2")


async def test_use_effect_callback_occurs_after_full_render_is_complete():
    effect_triggered = idom.Ref(False)
    effect_triggers_after_final_render = idom.Ref(None)

    @idom.component
    def OuterComponent():
        return idom.html.div(
            ComponentWithEffect(),
            CheckNoEffectYet(),
        )

    @idom.component
    def ComponentWithEffect():
        @idom.hooks.use_effect
        def effect():
            effect_triggered.current = True

        return idom.html.div()

    @idom.component
    def CheckNoEffectYet():
        effect_triggers_after_final_render.current = not effect_triggered.current
        return idom.html.div()

    with idom.Layout(OuterComponent()) as layout:
        await layout.render()

    assert effect_triggered.current
    assert effect_triggers_after_final_render.current is not None
    assert effect_triggers_after_final_render.current


async def test_use_effect_cleanup_occurs_before_next_effect():
    component_hook = HookCatcher()
    cleanup_triggered = idom.Ref(False)
    cleanup_triggered_before_next_effect = idom.Ref(False)

    @idom.component
    @component_hook.capture
    def ComponentWithEffect():
        @idom.hooks.use_effect(dependencies=None)
        def effect():
            if cleanup_triggered.current:
                cleanup_triggered_before_next_effect.current = True

            def cleanup():
                cleanup_triggered.current = True

            return cleanup

        return idom.html.div()

    with idom.Layout(ComponentWithEffect()) as layout:
        await layout.render()

        assert not cleanup_triggered.current

        component_hook.latest.schedule_render()
        await layout.render()

        assert cleanup_triggered.current
        assert cleanup_triggered_before_next_effect.current


async def test_use_effect_cleanup_occurs_on_will_unmount():
    set_key = idom.Ref()
    component_did_render = idom.Ref(False)
    cleanup_triggered = idom.Ref(False)
    cleanup_triggered_before_next_render = idom.Ref(False)

    @idom.component
    def OuterComponent():
        key, set_key.current = idom.use_state("first")
        return ComponentWithEffect(key=key)

    @idom.component
    def ComponentWithEffect():
        if component_did_render.current and cleanup_triggered.current:
            cleanup_triggered_before_next_render.current = True

        component_did_render.current = True

        @idom.hooks.use_effect
        def effect():
            def cleanup():
                cleanup_triggered.current = True

            return cleanup

        return idom.html.div()

    with idom.Layout(OuterComponent()) as layout:
        await layout.render()

        assert not cleanup_triggered.current

        set_key.current("second")
        await layout.render()

        assert cleanup_triggered.current
        assert cleanup_triggered_before_next_render.current


async def test_memoized_effect_on_recreated_if_dependencies_change():
    component_hook = HookCatcher()
    set_state_callback = idom.Ref(None)
    effect_run_count = idom.Ref(0)

    first_value = 1
    second_value = 2

    @idom.component
    @component_hook.capture
    def ComponentWithMemoizedEffect():
        state, set_state_callback.current = idom.hooks.use_state(first_value)

        @idom.hooks.use_effect(dependencies=[state])
        def effect():
            effect_run_count.current += 1

        return idom.html.div()

    with idom.Layout(ComponentWithMemoizedEffect()) as layout:
        await layout.render()

        assert effect_run_count.current == 1

        component_hook.latest.schedule_render()
        await layout.render()

        assert effect_run_count.current == 1

        set_state_callback.current(second_value)
        await layout.render()

        assert effect_run_count.current == 2

        component_hook.latest.schedule_render()
        await layout.render()

        assert effect_run_count.current == 2


async def test_memoized_effect_cleanup_only_triggered_before_new_effect():
    component_hook = HookCatcher()
    set_state_callback = idom.Ref(None)
    cleanup_trigger_count = idom.Ref(0)

    first_value = 1
    second_value = 2

    @idom.component
    @component_hook.capture
    def ComponentWithEffect():
        state, set_state_callback.current = idom.hooks.use_state(first_value)

        @idom.hooks.use_effect(dependencies=[state])
        def effect():
            def cleanup():
                cleanup_trigger_count.current += 1

            return cleanup

        return idom.html.div()

    with idom.Layout(ComponentWithEffect()) as layout:
        await layout.render()

        assert cleanup_trigger_count.current == 0

        component_hook.latest.schedule_render()
        await layout.render()

        assert cleanup_trigger_count.current == 0

        set_state_callback.current(second_value)
        await layout.render()

        assert cleanup_trigger_count.current == 1


async def test_use_async_effect():
    effect_ran = asyncio.Event()

    @idom.component
    def ComponentWithAsyncEffect():
        @idom.hooks.use_effect
        async def effect():
            effect_ran.set()

        return idom.html.div()

    with idom.Layout(ComponentWithAsyncEffect()) as layout:
        await layout.render()
        await asyncio.wait_for(effect_ran.wait(), 1)


async def test_use_async_effect_cleanup():
    component_hook = HookCatcher()
    effect_ran = asyncio.Event()
    cleanup_ran = asyncio.Event()

    @idom.component
    @component_hook.capture
    def ComponentWithAsyncEffect():
        @idom.hooks.use_effect(dependencies=None)  # force this to run every time
        async def effect():
            effect_ran.set()
            return cleanup_ran.set

        return idom.html.div()

    with idom.Layout(ComponentWithAsyncEffect()) as layout:
        await layout.render()

        component_hook.latest.schedule_render()

        await layout.render()

    await asyncio.wait_for(cleanup_ran.wait(), 1)


async def test_use_async_effect_cancel(caplog):
    component_hook = HookCatcher()
    effect_ran = asyncio.Event()
    effect_was_cancelled = asyncio.Event()

    event_that_never_occurs = asyncio.Event()

    @idom.component
    @component_hook.capture
    def ComponentWithLongWaitingEffect():
        @idom.hooks.use_effect(dependencies=None)  # force this to run every time
        async def effect():
            effect_ran.set()
            try:
                await event_that_never_occurs.wait()
            except asyncio.CancelledError:
                effect_was_cancelled.set()
                raise

        return idom.html.div()

    with idom.Layout(ComponentWithLongWaitingEffect()) as layout:
        await layout.render()

        await effect_ran.wait()
        component_hook.latest.schedule_render()

        await layout.render()

    await asyncio.wait_for(effect_was_cancelled.wait(), 1)

    # So I know we said the event never occurs but... to ensure the effect's future is
    # cancelled before the test is cleaned up we need to set the event. This is because
    # the cancellation doesn't propogate before the test is resolved which causes
    # delayed log messages that impact other tests.
    event_that_never_occurs.set()


async def test_error_in_effect_is_gracefully_handled(caplog):
    @idom.component
    def ComponentWithEffect():
        @idom.hooks.use_effect
        def bad_effect():
            raise ValueError("Something went wong :(")

        return idom.html.div()

    with idom.Layout(ComponentWithEffect()) as layout:
        await layout.render()  # no error

    first_log_line = next(iter(caplog.records)).msg.split("\n", 1)[0]
    assert re.match("Post-render effect .*? failed", first_log_line)


async def test_error_in_effect_cleanup_is_gracefully_handled(caplog):
    caplog.clear()
    component_hook = HookCatcher()

    @idom.component
    @component_hook.capture
    def ComponentWithEffect():
        @idom.hooks.use_effect(dependencies=None)  # force this to run every time
        def ok_effect():
            def bad_cleanup():
                raise ValueError("Something went wong :(")

            return bad_cleanup

        return idom.html.div()

    with idom.Layout(ComponentWithEffect()) as layout:
        await layout.render()
        component_hook.latest.schedule_render()
        await layout.render()  # no error

    first_log_line = next(iter(caplog.records)).msg.split("\n", 1)[0]
    assert re.match("Post-render effect .*?", first_log_line)


async def test_error_in_effect_pre_unmount_cleanup_is_gracefully_handled():
    set_key = idom.Ref()

    @idom.component
    def OuterComponent():
        key, set_key.current = idom.use_state("first")
        return ComponentWithEffect(key=key)

    @idom.component
    def ComponentWithEffect():
        @idom.hooks.use_effect
        def ok_effect():
            def bad_cleanup():
                raise ValueError("Something went wong :(")

            return bad_cleanup

        return idom.html.div()

    with assert_idom_logged(
        match_message=r"Pre-unmount effect .*? failed",
        error_type=ValueError,
    ):
        with idom.Layout(OuterComponent()) as layout:
            await layout.render()
            set_key.current("second")
            await layout.render()  # no error


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

    @idom.component
    def Counter(initial_count):
        saved_count.current, saved_dispatch.current = idom.hooks.use_reducer(
            reducer, initial_count
        )
        return idom.html.div()

    with idom.Layout(Counter(0)) as layout:
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

    @idom.component
    def ComponentWithUseReduce():
        saved_dispatchers.append(idom.hooks.use_reducer(reducer, 0)[1])
        return idom.html.div()

    with idom.Layout(ComponentWithUseReduce()) as layout:
        for _ in range(3):
            await layout.render()
            saved_dispatchers[-1]("increment")

    first_dispatch = saved_dispatchers[0]
    for d in saved_dispatchers[1:]:
        assert first_dispatch is d


async def test_use_callback_identity():
    component_hook = HookCatcher()
    used_callbacks = []

    @idom.component
    @component_hook.capture
    def ComponentWithRef():
        used_callbacks.append(idom.hooks.use_callback(lambda: None))
        return idom.html.div()

    with idom.Layout(ComponentWithRef()) as layout:
        await layout.render()
        component_hook.latest.schedule_render()
        await layout.render()

    assert used_callbacks[0] is used_callbacks[1]
    assert len(used_callbacks) == 2


async def test_use_callback_memoization():
    component_hook = HookCatcher()
    set_state_hook = idom.Ref(None)
    used_callbacks = []

    @idom.component
    @component_hook.capture
    def ComponentWithRef():
        state, set_state_hook.current = idom.hooks.use_state(0)

        @idom.hooks.use_callback(dependencies=[state])  # use the deco form for coverage
        def cb():
            return None

        used_callbacks.append(cb)
        return idom.html.div()

    with idom.Layout(ComponentWithRef()) as layout:
        await layout.render()
        set_state_hook.current(1)
        await layout.render()
        component_hook.latest.schedule_render()
        await layout.render()

    assert used_callbacks[0] is not used_callbacks[1]
    assert used_callbacks[1] is used_callbacks[2]
    assert len(used_callbacks) == 3


async def test_use_memo():
    component_hook = HookCatcher()
    set_state_hook = idom.Ref(None)
    used_values = []

    @idom.component
    @component_hook.capture
    def ComponentWithMemo():
        state, set_state_hook.current = idom.hooks.use_state(0)
        value = idom.hooks.use_memo(
            lambda: idom.Ref(state),  # use a Ref here just to ensure it's a unique obj
            [state],
        )
        used_values.append(value)
        return idom.html.div()

    with idom.Layout(ComponentWithMemo()) as layout:
        await layout.render()
        set_state_hook.current(1)
        await layout.render()
        component_hook.latest.schedule_render()
        await layout.render()

    assert used_values[0] is not used_values[1]
    assert used_values[1] is used_values[2]
    assert len(used_values) == 3


async def test_use_memo_always_runs_if_dependencies_are_none():
    component_hook = HookCatcher()
    used_values = []

    iter_values = iter([1, 2, 3])

    @idom.component
    @component_hook.capture
    def ComponentWithMemo():
        value = idom.hooks.use_memo(lambda: next(iter_values), dependencies=None)
        used_values.append(value)
        return idom.html.div()

    with idom.Layout(ComponentWithMemo()) as layout:
        await layout.render()
        component_hook.latest.schedule_render()
        await layout.render()
        component_hook.latest.schedule_render()
        await layout.render()

    assert used_values == [1, 2, 3]


async def test_use_memo_with_stored_deps_is_empty_tuple_after_deps_are_none():
    component_hook = HookCatcher()
    used_values = []

    iter_values = iter([1, 2, 3])
    deps_used_in_memo = idom.Ref(())

    @idom.component
    @component_hook.capture
    def ComponentWithMemo():
        value = idom.hooks.use_memo(
            lambda: next(iter_values),
            deps_used_in_memo.current,  # noqa: ROH202
        )
        used_values.append(value)
        return idom.html.div()

    with idom.Layout(ComponentWithMemo()) as layout:
        await layout.render()
        component_hook.latest.schedule_render()
        deps_used_in_memo.current = None
        await layout.render()
        component_hook.latest.schedule_render()
        deps_used_in_memo.current = ()
        await layout.render()

    assert used_values == [1, 2, 2]


async def test_use_memo_never_runs_if_deps_is_empty_list():
    component_hook = HookCatcher()
    used_values = []

    iter_values = iter([1, 2, 3])

    @idom.component
    @component_hook.capture
    def ComponentWithMemo():
        value = idom.hooks.use_memo(lambda: next(iter_values), ())
        used_values.append(value)
        return idom.html.div()

    with idom.Layout(ComponentWithMemo()) as layout:
        await layout.render()
        component_hook.latest.schedule_render()
        await layout.render()
        component_hook.latest.schedule_render()
        await layout.render()

    assert used_values == [1, 1, 1]


async def test_use_ref():
    component_hook = HookCatcher()
    used_refs = []

    @idom.component
    @component_hook.capture
    def ComponentWithRef():
        used_refs.append(idom.hooks.use_ref(1))
        return idom.html.div()

    with idom.Layout(ComponentWithRef()) as layout:
        await layout.render()
        component_hook.latest.schedule_render()
        await layout.render()

    assert used_refs[0] is used_refs[1]
    assert len(used_refs) == 2


def test_bad_schedule_render_callback(caplog):
    def bad_callback():
        raise ValueError("something went wrong")

    hook = LifeCycleHook(bad_callback)

    hook.schedule_render()

    first_log_line = next(iter(caplog.records)).msg.split("\n", 1)[0]
    assert re.match(f"Failed to schedule render via {bad_callback}", first_log_line)


async def test_use_effect_automatically_infers_closure_values():
    set_count = idom.Ref()
    did_effect = asyncio.Event()

    @idom.component
    def CounterWithEffect():
        count, set_count.current = idom.hooks.use_state(0)

        @idom.hooks.use_effect
        def some_effect_that_uses_count():
            """should automatically trigger on count change"""
            count  # use count in this closure
            did_effect.set()

        return idom.html.div()

    with idom.Layout(CounterWithEffect()) as layout:
        await layout.render()
        await did_effect.wait()
        did_effect.clear()

        for i in range(1, 3):
            set_count.current(i)
            await layout.render()
            await did_effect.wait()
            did_effect.clear()


async def test_use_memo_automatically_infers_closure_values():
    set_count = idom.Ref()
    did_memo = asyncio.Event()

    @idom.component
    def CounterWithEffect():
        count, set_count.current = idom.hooks.use_state(0)

        @idom.hooks.use_memo
        def some_memo_func_that_uses_count():
            """should automatically trigger on count change"""
            count  # use count in this closure
            did_memo.set()

        return idom.html.div()

    with idom.Layout(CounterWithEffect()) as layout:
        await layout.render()
        await did_memo.wait()
        did_memo.clear()

        for i in range(1, 3):
            set_count.current(i)
            await layout.render()
            await did_memo.wait()
            did_memo.clear()
