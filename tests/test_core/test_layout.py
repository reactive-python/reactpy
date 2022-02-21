import asyncio
import gc
import random
import re
from weakref import finalize
from weakref import ref as weakref

import pytest

import idom
from idom import html
from idom.config import IDOM_DEBUG_MODE
from idom.core.component import component
from idom.core.dispatcher import render_json_patch
from idom.core.hooks import use_effect, use_state
from idom.core.layout import Layout, LayoutEvent
from idom.testing import (
    HookCatcher,
    StaticEventHandler,
    assert_idom_logged,
    capture_idom_logs,
)
from idom.utils import Ref
from tests.assert_utils import assert_same_items


@pytest.fixture(autouse=True)
def no_logged_errors():
    with capture_idom_logs() as logs:
        yield
        for record in logs:
            if record.exc_info:
                raise record.exc_info[1]


def test_layout_repr():
    @idom.component
    def MyComponent():
        ...

    my_component = MyComponent()
    layout = idom.Layout(my_component)
    assert str(layout) == f"Layout(MyComponent({id(my_component):02x}))"


def test_layout_expects_abstract_component():
    with pytest.raises(TypeError, match="Expected a ComponentType"):
        idom.Layout(None)
    with pytest.raises(TypeError, match="Expected a ComponentType"):
        idom.Layout(idom.html.div())


async def test_layout_cannot_be_used_outside_context_manager(caplog):
    @idom.component
    def Component():
        ...

    component = Component()
    layout = idom.Layout(component)

    with pytest.raises(Exception):
        await layout.deliver(LayoutEvent("something", []))

    with pytest.raises(Exception):
        layout.update(component)

    with pytest.raises(Exception):
        await layout.render()


async def test_simple_layout():
    set_state_hook = idom.Ref(None)

    @idom.component
    def SimpleComponent():
        tag, set_state_hook.current = idom.hooks.use_state("div")
        return idom.vdom(tag)

    with idom.Layout(SimpleComponent()) as layout:
        path, changes = await render_json_patch(layout)

        assert path == ""
        assert_same_items(
            changes,
            [
                {"op": "add", "path": "/children", "value": [{"tagName": "div"}]},
                {"op": "add", "path": "/tagName", "value": ""},
            ],
        )

        set_state_hook.current("table")
        path, changes = await render_json_patch(layout)

        assert path == ""
        assert changes == [
            {"op": "replace", "path": "/children/0/tagName", "value": "table"}
        ]


async def test_component_can_return_none():
    @idom.component
    def SomeComponent():
        return None

    with idom.Layout(SomeComponent()) as layout:
        assert (await layout.render()).new == {"tagName": ""}


async def test_nested_component_layout():
    parent_set_state = idom.Ref(None)
    child_set_state = idom.Ref(None)

    @idom.component
    def Parent():
        state, parent_set_state.current = idom.hooks.use_state(0)
        return idom.html.div(state, Child(key="c"))

    @idom.component
    def Child():
        state, child_set_state.current = idom.hooks.use_state(0)
        return idom.html.div(state)

    with idom.Layout(Parent(key="p")) as layout:
        path, changes = await render_json_patch(layout)

        assert path == ""
        assert_same_items(
            changes,
            [
                {
                    "op": "add",
                    "path": "/children",
                    "value": [
                        {
                            "children": [
                                "0",
                                {
                                    "children": [{"children": ["0"], "tagName": "div"}],
                                    "tagName": "",
                                },
                            ],
                            "tagName": "div",
                        }
                    ],
                },
                {"op": "add", "path": "/tagName", "value": ""},
            ],
        )

        parent_set_state.current(1)
        path, changes = await render_json_patch(layout)

        assert path == ""
        assert changes == [
            {"op": "replace", "path": "/children/0/children/0", "value": "1"}
        ]

        child_set_state.current(1)
        path, changes = await render_json_patch(layout)

        assert path == "/children/0/children/1"
        assert changes == [
            {"op": "replace", "path": "/children/0/children/0", "value": "1"}
        ]


@pytest.mark.skipif(
    not IDOM_DEBUG_MODE.current,
    reason="errors only reported in debug mode",
)
async def test_layout_render_error_has_partial_update_with_error_message():
    @idom.component
    def Main():
        return idom.html.div([OkChild(), BadChild(), OkChild()])

    @idom.component
    def OkChild():
        return idom.html.div(["hello"])

    @idom.component
    def BadChild():
        raise ValueError("error from bad child")

    with assert_idom_logged(
        match_error="error from bad child",
        clear_matched_records=True,
    ):

        with idom.Layout(Main()) as layout:
            patch = await render_json_patch(layout)
            assert_same_items(
                patch.changes,
                [
                    {
                        "op": "add",
                        "path": "/children",
                        "value": [
                            {
                                "tagName": "div",
                                "children": [
                                    {
                                        "tagName": "",
                                        "children": [
                                            {"tagName": "div", "children": ["hello"]}
                                        ],
                                    },
                                    {
                                        "tagName": "",
                                        "error": "ValueError: error from bad child",
                                    },
                                    {
                                        "tagName": "",
                                        "children": [
                                            {"tagName": "div", "children": ["hello"]}
                                        ],
                                    },
                                ],
                            }
                        ],
                    },
                    {"op": "add", "path": "/tagName", "value": ""},
                ],
            )


@pytest.mark.skipif(
    IDOM_DEBUG_MODE.current,
    reason="errors only reported in debug mode",
)
async def test_layout_render_error_has_partial_update_without_error_message():
    @idom.component
    def Main():
        return idom.html.div([OkChild(), BadChild(), OkChild()])

    @idom.component
    def OkChild():
        return idom.html.div(["hello"])

    @idom.component
    def BadChild():
        raise ValueError("error from bad child")

    with assert_idom_logged(
        match_error="error from bad child",
        clear_matched_records=True,
    ):

        with idom.Layout(Main()) as layout:
            patch = await render_json_patch(layout)
            assert_same_items(
                patch.changes,
                [
                    {
                        "op": "add",
                        "path": "/children",
                        "value": [
                            {
                                "children": [
                                    {
                                        "children": [
                                            {"children": ["hello"], "tagName": "div"}
                                        ],
                                        "tagName": "",
                                    },
                                    {"error": "", "tagName": ""},
                                    {
                                        "children": [
                                            {"children": ["hello"], "tagName": "div"}
                                        ],
                                        "tagName": "",
                                    },
                                ],
                                "tagName": "div",
                            }
                        ],
                    },
                    {"op": "add", "path": "/tagName", "value": ""},
                ],
            )


async def test_render_raw_vdom_dict_with_single_component_object_as_children():
    @idom.component
    def Main():
        return {"tagName": "div", "children": Child()}

    @idom.component
    def Child():
        return {"tagName": "div", "children": {"tagName": "h1"}}

    with idom.Layout(Main()) as layout:
        patch = await render_json_patch(layout)
        assert_same_items(
            patch.changes,
            [
                {
                    "op": "add",
                    "path": "/children",
                    "value": [
                        {
                            "children": [
                                {
                                    "children": [
                                        {
                                            "children": [{"tagName": "h1"}],
                                            "tagName": "div",
                                        }
                                    ],
                                    "tagName": "",
                                }
                            ],
                            "tagName": "div",
                        }
                    ],
                },
                {"op": "add", "path": "/tagName", "value": ""},
            ],
        )


async def test_components_are_garbage_collected():
    live_components = set()
    outer_component_hook = HookCatcher()

    def add_to_live_components(constructor):
        def wrapper(*args, **kwargs):
            component = constructor(*args, **kwargs)
            component_id = id(component)
            live_components.add(component_id)
            finalize(component, live_components.discard, component_id)
            return component

        return wrapper

    @add_to_live_components
    @idom.component
    @outer_component_hook.capture
    def Outer():
        return Inner()

    @add_to_live_components
    @idom.component
    def Inner():
        return idom.html.div()

    with idom.Layout(Outer()) as layout:
        await layout.render()

        assert len(live_components) == 2

        last_live_components = live_components.copy()
        # The existing `Outer` component rerenders. A new `Inner` component is created and
        # the the old `Inner` component should be deleted. Thus there should be one
        # changed component in the set of `live_components` the old `Inner` deleted and new
        # `Inner` added.
        outer_component_hook.latest.schedule_render()
        await layout.render()

        assert len(live_components - last_live_components) == 1

    # The layout still holds a reference to the root so that's
    # only deleted once we release our reference to the layout.
    del layout
    # the hook also contains a reference to the root component
    del outer_component_hook

    assert not live_components


async def test_root_component_life_cycle_hook_is_garbage_collected():
    live_hooks = set()

    def add_to_live_hooks(constructor):
        def wrapper(*args, **kwargs):
            result = constructor(*args, **kwargs)
            hook = idom.hooks.current_hook()
            hook_id = id(hook)
            live_hooks.add(hook_id)
            finalize(hook, live_hooks.discard, hook_id)
            return result

        return wrapper

    @idom.component
    @add_to_live_hooks
    def Root():
        return idom.html.div()

    with idom.Layout(Root()) as layout:
        await layout.render()

        assert len(live_hooks) == 1

    # The layout still holds a reference to the root so that's only deleted once we
    # release our reference to the layout.
    del layout

    assert not live_hooks


async def test_life_cycle_hooks_are_garbage_collected():
    live_hooks = set()
    set_inner_component = None

    def add_to_live_hooks(constructor):
        def wrapper(*args, **kwargs):
            result = constructor(*args, **kwargs)
            hook = idom.hooks.current_hook()
            hook_id = id(hook)
            live_hooks.add(hook_id)
            finalize(hook, live_hooks.discard, hook_id)
            return result

        return wrapper

    @idom.component
    @add_to_live_hooks
    def Outer():
        nonlocal set_inner_component
        inner_component, set_inner_component = idom.hooks.use_state(Inner(key="first"))
        return inner_component

    @idom.component
    @add_to_live_hooks
    def Inner():
        return idom.html.div()

    with idom.Layout(Outer()) as layout:
        await layout.render()

        assert len(live_hooks) == 2
        last_live_hooks = live_hooks.copy()

        # We expect the hook for `InnerOne` to be garbage collected since the component
        # will get replaced.
        set_inner_component(Inner(key="second"))
        await layout.render()
        assert len(live_hooks - last_live_hooks) == 1

    # The layout still holds a reference to the root so that's only deleted once we
    # release our reference to the layout.
    del layout
    del set_inner_component

    # For some reason, holding `set_inner_component` outside the render context causes
    # the associated hook to not be automatically garbage collected. After some
    # imperical investigation, it seems that if we do not hold `set_inner_component` in
    # this way, the call to `gc.collect()` isn't required. This is demonstrated in
    # `test_root_component_life_cycle_hook_is_garbage_collected`
    gc.collect()

    assert not live_hooks


async def test_double_updated_component_is_not_double_rendered():
    hook = HookCatcher()
    run_count = idom.Ref(0)

    @idom.component
    @hook.capture
    def AnyComponent():
        run_count.current += 1
        return idom.html.div()

    with idom.Layout(AnyComponent()) as layout:
        await layout.render()

        assert run_count.current == 1

        hook.latest.schedule_render()
        hook.latest.schedule_render()

        await layout.render()
        try:
            await asyncio.wait_for(
                layout.render(),
                timeout=0.1,  # this should have been plenty of time
            )
        except asyncio.TimeoutError:
            pass  # the render should still be rendering since we only update once

        assert run_count.current == 2


async def test_update_path_to_component_that_is_not_direct_child_is_correct():
    hook = HookCatcher()

    @idom.component
    def Parent():
        return idom.html.div(idom.html.div(Child()))

    @idom.component
    @hook.capture
    def Child():
        return idom.html.div()

    with idom.Layout(Parent()) as layout:
        await layout.render()

        hook.latest.schedule_render()

        update = await render_json_patch(layout)
        assert update.path == "/children/0/children/0/children/0"


async def test_log_on_dispatch_to_missing_event_handler(caplog):
    @idom.component
    def SomeComponent():
        return idom.html.div()

    with idom.Layout(SomeComponent()) as layout:
        await layout.deliver(LayoutEvent(target="missing", data=[]))

    assert re.match(
        "Ignored event - handler 'missing' does not exist or its component unmounted",
        next(iter(caplog.records)).msg,
    )


def use_toggle(init=False):
    state, set_state = idom.hooks.use_state(init)
    return state, lambda: set_state(lambda old: not old)


async def test_model_key_preserves_callback_identity_for_common_elements(caplog):
    called_good_trigger = idom.Ref(False)
    good_handler = StaticEventHandler()
    bad_handler = StaticEventHandler()

    @idom.component
    def MyComponent():
        reverse_children, set_reverse_children = use_toggle()

        @good_handler.use
        def good_trigger():
            called_good_trigger.current = True
            set_reverse_children()

        @bad_handler.use
        def bad_trigger():
            raise ValueError("Called bad trigger")

        children = [
            idom.html.button(
                {"onClick": good_trigger, "id": "good"}, "good", key="good"
            ),
            idom.html.button({"onClick": bad_trigger, "id": "bad"}, "bad", key="bad"),
        ]

        if reverse_children:
            children.reverse()

        return idom.html.div(children)

    with idom.Layout(MyComponent()) as layout:
        await layout.render()
        for i in range(3):
            event = LayoutEvent(good_handler.target, [])
            await layout.deliver(event)

            assert called_good_trigger.current
            # reset after checking
            called_good_trigger.current = False

            await layout.render()

    assert not caplog.records


async def test_model_key_preserves_callback_identity_for_components():
    called_good_trigger = idom.Ref(False)
    good_handler = StaticEventHandler()
    bad_handler = StaticEventHandler()

    @idom.component
    def RootComponent():
        reverse_children, set_reverse_children = use_toggle()

        children = [
            Trigger(set_reverse_children, name=name, key=name)
            for name in ["good", "bad"]
        ]

        if reverse_children:
            children.reverse()

        return idom.html.div(children)

    @idom.component
    def Trigger(set_reverse_children, name):
        if name == "good":

            @good_handler.use
            def callback():
                called_good_trigger.current = True
                set_reverse_children()

        else:

            @bad_handler.use
            def callback():
                raise ValueError("Called bad trigger")

        return idom.html.button({"onClick": callback, "id": "good"}, "good")

    with idom.Layout(RootComponent()) as layout:
        await layout.render()
        for _ in range(3):
            event = LayoutEvent(good_handler.target, [])
            await layout.deliver(event)

            assert called_good_trigger.current
            # reset after checking
            called_good_trigger.current = False

            await layout.render()


async def test_component_can_return_another_component_directly():
    @idom.component
    def Outer():
        return Inner()

    @idom.component
    def Inner():
        return idom.html.div("hello")

    with idom.Layout(Outer()) as layout:
        update = await render_json_patch(layout)
        assert_same_items(
            update.changes,
            [
                {
                    "op": "add",
                    "path": "/children",
                    "value": [
                        {
                            "children": [{"children": ["hello"], "tagName": "div"}],
                            "tagName": "",
                        }
                    ],
                },
                {"op": "add", "path": "/tagName", "value": ""},
            ],
        )


async def test_hooks_for_keyed_components_get_garbage_collected():
    pop_item = idom.Ref(None)
    garbage_collect_items = []
    registered_finalizers = set()

    @idom.component
    def Outer():
        items, set_items = idom.hooks.use_state([1, 2, 3])
        pop_item.current = lambda: set_items(items[:-1])
        return idom.html.div(Inner(key=k, finalizer_id=k) for k in items)

    @idom.component
    def Inner(finalizer_id):
        if finalizer_id not in registered_finalizers:
            hook = idom.hooks.current_hook()
            finalize(hook, lambda: garbage_collect_items.append(finalizer_id))
            registered_finalizers.add(finalizer_id)
        return idom.html.div(finalizer_id)

    with idom.Layout(Outer()) as layout:
        await layout.render()

        pop_item.current()
        await layout.render()
        assert garbage_collect_items == [3]

        pop_item.current()
        await layout.render()
        assert garbage_collect_items == [3, 2]

        pop_item.current()
        await layout.render()
        assert garbage_collect_items == [3, 2, 1]


async def test_event_handler_at_component_root_is_garbage_collected():
    event_handler = idom.Ref()

    @idom.component
    def HasEventHandlerAtRoot():
        value, set_value = idom.hooks.use_state(False)
        set_value(not value)  # trigger renders forever
        event_handler.current = weakref(set_value)
        button = idom.html.button({"onClick": set_value}, "state is: ", value)
        event_handler.current = weakref(button["eventHandlers"]["onClick"].function)
        return button

    with idom.Layout(HasEventHandlerAtRoot()) as layout:
        await layout.render()

        for i in range(3):
            last_event_handler = event_handler.current
            # after this render we should have release the reference to the last handler
            await layout.render()
            assert last_event_handler() is None


async def test_event_handler_deep_in_component_layout_is_garbage_collected():
    event_handler = idom.Ref()

    @idom.component
    def HasNestedEventHandler():
        value, set_value = idom.hooks.use_state(False)
        set_value(not value)  # trigger renders forever
        event_handler.current = weakref(set_value)
        button = idom.html.button({"onClick": set_value}, "state is: ", value)
        event_handler.current = weakref(button["eventHandlers"]["onClick"].function)
        return idom.html.div(idom.html.div(button))

    with idom.Layout(HasNestedEventHandler()) as layout:
        await layout.render()

        for i in range(3):
            last_event_handler = event_handler.current
            # after this render we should have release the reference to the last handler
            await layout.render()
            assert last_event_handler() is None


async def test_duplicate_sibling_keys_causes_error(caplog):
    hook = HookCatcher()
    should_error = True

    @idom.component
    @hook.capture
    def ComponentReturnsDuplicateKeys():
        if should_error:
            return idom.html.div(
                idom.html.div(key="duplicate"),
                idom.html.div(key="duplicate"),
            )
        else:
            return idom.html.div()

    with idom.Layout(ComponentReturnsDuplicateKeys()) as layout:
        with assert_idom_logged(
            error_type=ValueError,
            match_error=r"Duplicate keys \['duplicate'\] at '/children/0'",
            clear_matched_records=True,
        ):
            await layout.render()

        hook.latest.schedule_render()

        should_error = False
        await layout.render()

        should_error = True
        hook.latest.schedule_render()
        with assert_idom_logged(
            error_type=ValueError,
            match_error=r"Duplicate keys \['duplicate'\] at '/children/0'",
            clear_matched_records=True,
        ):
            await layout.render()


async def test_keyed_components_preserve_hook_on_parent_update():
    outer_hook = HookCatcher()
    inner_hook = HookCatcher()

    @idom.component
    @outer_hook.capture
    def Outer():
        return Inner(key=1)

    @idom.component
    @inner_hook.capture
    def Inner():
        return idom.html.div()

    with idom.Layout(Outer()) as layout:
        await layout.render()
        old_inner_hook = inner_hook.latest

        outer_hook.latest.schedule_render()
        await layout.render()
        assert old_inner_hook is inner_hook.latest


async def test_log_error_on_bad_event_handler():
    bad_handler = StaticEventHandler()

    @idom.component
    def ComponentWithBadEventHandler():
        @bad_handler.use
        def raise_error():
            raise Exception("bad event handler")

        return idom.html.button({"onClick": raise_error})

    with assert_idom_logged(
        match_error="bad event handler",
        clear_matched_records=True,
    ):

        with idom.Layout(ComponentWithBadEventHandler()) as layout:
            await layout.render()
            event = LayoutEvent(bad_handler.target, [])
            await layout.deliver(event)


async def test_schedule_render_from_unmounted_hook(caplog):
    parent_set_state = idom.Ref()

    @idom.component
    def Parent():
        state, parent_set_state.current = idom.hooks.use_state(1)
        return Child(key=state, state=state)

    child_hook = HookCatcher()

    @idom.component
    @child_hook.capture
    def Child(state):
        idom.hooks.use_effect(lambda: lambda: print("unmount", state))
        return idom.html.div(state)

    with assert_idom_logged(
        r"Did not render component with model state ID .*? - component already unmounted",
    ):
        with idom.Layout(Parent()) as layout:
            await layout.render()

            old_hook = child_hook.latest

            # cause initial child to be unmounted
            parent_set_state.current(2)
            await layout.render()

            # trigger render for hook that's been unmounted
            old_hook.schedule_render()

            # schedule one more render just to make it so `layout.render()` doesn't hang
            # when the scheduled render above gets skipped
            parent_set_state.current(3)

            await layout.render()


async def test_elements_and_components_with_the_same_key_can_be_interchanged():
    set_toggle = idom.Ref()
    effects = []

    def use_toggle():
        state, set_state = idom.hooks.use_state(True)
        return state, lambda: set_state(not state)

    @idom.component
    def Root():
        toggle, set_toggle.current = use_toggle()
        if toggle:
            return SomeComponent("x")
        else:
            return idom.html.div(SomeComponent("y"))

    @idom.component
    def SomeComponent(name):
        @use_effect
        def some_effect():
            effects.append("mount " + name)
            return lambda: effects.append("unmount " + name)

        return idom.html.div(name)

    with idom.Layout(Root()) as layout:
        await layout.render()

        assert effects == ["mount x"]

        set_toggle.current()
        await layout.render()

        assert effects == ["mount x", "unmount x", "mount y"]

        set_toggle.current()
        await layout.render()

        assert effects == ["mount x", "unmount x", "mount y", "unmount y", "mount x"]


async def test_layout_does_not_copy_element_children_by_key():
    # this is a regression test for a subtle bug:
    # https://github.com/idom-team/idom/issues/556

    set_items = idom.Ref()

    @idom.component
    def SomeComponent():
        items, set_items.current = idom.use_state([1, 2, 3])
        return idom.html.div(
            [
                idom.html.div(
                    idom.html.input({"onChange": lambda event: None}),
                    key=str(i),
                )
                for i in items
            ]
        )

    with idom.Layout(SomeComponent()) as layout:
        await layout.render()

        set_items.current([2, 3])

        await layout.render()

        set_items.current([3])

        await layout.render()

        set_items.current([])

        await layout.render()


async def test_changing_key_of_parent_element_unmounts_children():
    random.seed(0)

    root_hook = HookCatcher()
    state = idom.Ref(None)

    @idom.component
    @root_hook.capture
    def Root():
        return idom.html.div(HasState(), key=str(random.random()))

    @idom.component
    def HasState():
        state.current = idom.hooks.use_state(random.random)[0]
        return idom.html.div()

    with idom.Layout(Root()) as layout:
        await layout.render()

        for i in range(5):
            last_state = state.current
            root_hook.latest.schedule_render()
            await layout.render()
            assert last_state != state.current


async def test_switching_node_type_with_event_handlers():
    toggle_type = idom.Ref()
    element_static_handler = StaticEventHandler()
    component_static_handler = StaticEventHandler()

    @idom.component
    def Root():
        toggle, toggle_type.current = use_toggle(True)
        handler = element_static_handler.use(lambda: None)
        if toggle:
            return html.div(html.button({"onEvent": handler}))
        else:
            return html.div(SomeComponent())

    @idom.component
    def SomeComponent():
        handler = component_static_handler.use(lambda: None)
        return html.button({"onAnotherEvent": handler})

    with idom.Layout(Root()) as layout:
        await layout.render()

        assert element_static_handler.target in layout._event_handlers
        assert component_static_handler.target not in layout._event_handlers

        toggle_type.current()
        await layout.render()

        assert element_static_handler.target not in layout._event_handlers
        assert component_static_handler.target in layout._event_handlers

        toggle_type.current()
        await layout.render()

        assert element_static_handler.target in layout._event_handlers
        assert component_static_handler.target not in layout._event_handlers


async def test_switching_component_definition():
    toggle_component = idom.Ref()
    first_used_state = idom.Ref(None)
    second_used_state = idom.Ref(None)

    @idom.component
    def Root():
        toggle, toggle_component.current = use_toggle(True)
        if toggle:
            return FirstComponent()
        else:
            return SecondComponent()

    @idom.component
    def FirstComponent():
        first_used_state.current = use_state("first")[0]
        # reset state after unmount
        use_effect(lambda: lambda: first_used_state.set_current(None))
        return html.div()

    @idom.component
    def SecondComponent():
        second_used_state.current = use_state("second")[0]
        # reset state after unmount
        use_effect(lambda: lambda: second_used_state.set_current(None))
        return html.div()

    with idom.Layout(Root()) as layout:
        await layout.render()

        assert first_used_state.current == "first"
        assert second_used_state.current is None

        toggle_component.current()
        await layout.render()

        assert first_used_state.current is None
        assert second_used_state.current == "second"

        toggle_component.current()
        await layout.render()

        assert first_used_state.current == "first"
        assert second_used_state.current is None


async def test_element_keys_inside_components_do_not_reset_state_of_component():
    """This is a regression test for a bug.

    You would not expect that calling `set_child_key_num` would trigger state to be
    reset in any `Child()` components but there was a bug where that happened.
    """

    effect_calls_without_state = []
    set_child_key_num = StaticEventHandler()
    did_call_effect = asyncio.Event()

    @component
    def Parent():
        state, set_state = use_state(0)
        return html.div(
            html.button(
                {"onClick": set_child_key_num.use(lambda: set_state(state + 1))},
                "click me",
            ),
            Child("some-key"),
            Child(f"key-{state}"),
        )

    @component
    def Child(child_key):
        state, set_state = use_state(0)

        @use_effect
        async def record_if_state_is_reset():
            if state:
                return
            effect_calls_without_state.append(child_key)
            set_state(1)
            did_call_effect.set()

        return html.div(
            child_key,
            key=child_key,
        )

    with idom.Layout(Parent()) as layout:
        await layout.render()
        await did_call_effect.wait()
        assert effect_calls_without_state == ["some-key", "key-0"]
        did_call_effect.clear()

        for i in range(1, 5):
            await layout.deliver(LayoutEvent(set_child_key_num.target, []))
            await layout.render()
            assert effect_calls_without_state == ["some-key", "key-0"]
            did_call_effect.clear()


async def test_changing_key_of_component_resets_state():
    set_key = Ref()
    did_init_state = Ref(0)
    hook = HookCatcher()

    @component
    @hook.capture
    def Root():
        key, set_key.current = use_state("key-1")
        return Child(key=key)

    @component
    def Child():
        use_state(lambda: did_init_state.set_current(did_init_state.current + 1))

    with Layout(Root()) as layout:
        await layout.render()
        assert did_init_state.current == 1

        set_key.current("key-2")
        await layout.render()
        assert did_init_state.current == 2

        hook.latest.schedule_render()
        await layout.render()
        assert did_init_state.current == 2


async def test_changing_event_handlers_in_the_next_render():
    set_event_name = Ref()
    event_handler = StaticEventHandler()
    did_trigger = Ref(False)

    @component
    def Root():
        event_name, set_event_name.current = use_state("first")
        return html.button(
            {event_name: event_handler.use(lambda: did_trigger.set_current(True))}
        )

    with Layout(Root()) as layout:
        await layout.render()
        await layout.deliver(LayoutEvent(event_handler.target, []))
        assert did_trigger.current
        did_trigger.current = False

        set_event_name.current("second")
        await layout.render()
        await layout.deliver(LayoutEvent(event_handler.target, []))
        assert did_trigger.current
        did_trigger.current = False


async def test_change_element_to_string_causes_unmount():
    set_toggle = Ref()
    did_unmount = Ref(False)

    @component
    def Root():
        toggle, set_toggle.current = use_toggle(True)
        if toggle:
            return html.div(Child())
        else:
            return html.div("some-string")

    @component
    def Child():
        use_effect(lambda: lambda: did_unmount.set_current(True))

    with Layout(Root()) as layout:
        await layout.render()

        set_toggle.current()

        await layout.render()

        assert did_unmount.current


class ComponentShouldRender:
    def __init__(self, child, should_render):
        self.child = child or html.div()
        self.should_render = should_render
        self.key = None
        self.type = self.__class__

    def render(self):
        return html.div(self.child)


async def test_component_should_render_always_true():
    render_count = idom.Ref(0)
    root_hook = HookCatcher()

    @idom.component
    @root_hook.capture
    def Root():
        return ComponentShouldRender(SomeComponent(), should_render=lambda new: True)

    @idom.component
    def SomeComponent():
        render_count.current += 1
        return html.div()

    with idom.Layout(Root()) as layout:
        for _ in range(4):
            await layout.render()
            root_hook.latest.schedule_render()

    assert render_count.current == 4


async def test_component_should_render_always_false():
    render_count = idom.Ref(0)
    root_hook = HookCatcher()

    @idom.component
    @root_hook.capture
    def Root():
        return ComponentShouldRender(SomeComponent(), should_render=lambda new: False)

    @idom.component
    def SomeComponent():
        render_count.current += 1
        return html.div()

    with idom.Layout(Root()) as layout:
        for _ in range(4):
            await layout.render()
            root_hook.latest.schedule_render()

    assert render_count.current == 1


async def test_component_error_in_should_render_is_handled_gracefully():
    root_hook = HookCatcher()

    @idom.component
    @root_hook.capture
    def Root():
        def bad_should_render(new):
            raise ValueError("The error message")

        return ComponentShouldRender(html.div(), should_render=bad_should_render)

    with assert_idom_logged(
        match_message=r".* component failed to check if .* should be rendered",
        error_type=ValueError,
        match_error="The error message",
        clear_matched_records=True,
    ):
        with idom.Layout(Root()) as layout:
            await layout.render()
            root_hook.latest.schedule_render()
            await layout.render()
