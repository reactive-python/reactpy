import asyncio
import gc
import re
from weakref import finalize

import pytest

import idom
from idom.core.dispatcher import render_json_patch
from idom.core.layout import LayoutEvent
from idom.testing import HookCatcher, StaticEventHandler
from tests.general_utils import assert_same_items


def test_layout_repr():
    @idom.component
    def MyComponent():
        ...

    my_component = MyComponent()
    layout = idom.Layout(my_component)
    assert str(layout) == f"Layout(MyComponent({id(my_component)}))"


def test_layout_expects_abstract_component():
    with pytest.raises(TypeError, match="Expected an ComponentType"):
        idom.Layout(None)
    with pytest.raises(TypeError, match="Expected an ComponentType"):
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
        await render_json_patch(layout)


async def test_simple_layout():
    set_state_hook = idom.Ref(None)

    @idom.component
    def SimpleComponent():
        tag, set_state_hook.current = idom.hooks.use_state("div")
        return idom.vdom(tag)

    with idom.Layout(SimpleComponent()) as layout:
        path, changes = await render_json_patch(layout)

        assert path == ""
        assert changes == [{"op": "add", "path": "/tagName", "value": "div"}]

        set_state_hook.current("table")
        path, changes = await render_json_patch(layout)

        assert path == ""
        assert changes == [{"op": "replace", "path": "/tagName", "value": "table"}]


async def test_nested_component_layout():
    parent_set_state = idom.Ref(None)
    child_set_state = idom.Ref(None)

    @idom.component
    def Parent(key):
        state, parent_set_state.current = idom.hooks.use_state(0)
        return idom.html.div(state, Child(key="c"))

    @idom.component
    def Child(key):
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
                    "value": ["0", {"tagName": "div", "children": ["0"]}],
                },
                {"op": "add", "path": "/tagName", "value": "div"},
            ],
        )

        parent_set_state.current(1)
        path, changes = await render_json_patch(layout)

        assert path == ""
        assert changes == [{"op": "replace", "path": "/children/0", "value": "1"}]

        child_set_state.current(1)
        path, changes = await render_json_patch(layout)

        assert path == "/children/1"
        assert changes == [{"op": "replace", "path": "/children/0", "value": "1"}]


async def test_layout_render_error_has_partial_update():
    @idom.component
    def Main():
        return idom.html.div([OkChild(), BadChild(), OkChild()])

    @idom.component
    def OkChild():
        return idom.html.div(["hello"])

    @idom.component
    def BadChild():
        raise ValueError("Something went wrong :(")

    with idom.Layout(Main()) as layout:
        patch = await render_json_patch(layout)
        assert_same_items(
            patch.changes,
            [
                {
                    "op": "add",
                    "path": "/children",
                    "value": [
                        {"tagName": "div", "children": ["hello"]},
                        {
                            "tagName": "__error__",
                            "children": ["Something went wrong :("],
                        },
                        {"tagName": "div", "children": ["hello"]},
                    ],
                },
                {"op": "add", "path": "/tagName", "value": "div"},
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
                    "value": [{"tagName": "div", "children": [{"tagName": "h1"}]}],
                },
                {"op": "add", "path": "/tagName", "value": "div"},
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
        await render_json_patch(layout)

        assert len(live_components) == 2

        last_live_components = live_components.copy()
        # The existing `Outer` component rerenders. A new `Inner` component is created and
        # the the old `Inner` component should be deleted. Thus there should be one
        # changed component in the set of `live_components` the old `Inner` deleted and new
        # `Inner` added.
        outer_component_hook.latest.schedule_render()
        await render_json_patch(layout)

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
        await render_json_patch(layout)

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
        inner_component, set_inner_component = idom.hooks.use_state(InnerOne())
        return inner_component

    @idom.component
    @add_to_live_hooks
    def InnerOne():
        return idom.html.div()

    @idom.component
    @add_to_live_hooks
    def InnerTwo():
        return idom.html.div()

    with idom.Layout(Outer()) as layout:
        await render_json_patch(layout)

        assert len(live_hooks) == 2
        last_live_hooks = live_hooks.copy()

        # We expect the hook for `InnerOne` to be garbage collected since it the
        # component will get replaced.
        set_inner_component(InnerTwo())
        await render_json_patch(layout)
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
        await render_json_patch(layout)

        assert run_count.current == 1

        hook.latest.schedule_render()
        hook.latest.schedule_render()

        await render_json_patch(layout)
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
        await render_json_patch(layout)

        hook.latest.schedule_render()

        update = await render_json_patch(layout)
        assert update.path == "/children/0/children/0"


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
        await render_json_patch(layout)
        for i in range(3):
            event = LayoutEvent(good_handler.target, [])
            await layout.deliver(event)

            assert called_good_trigger.current
            # reset after checking
            called_good_trigger.current = False

            await render_json_patch(layout)

    assert not caplog.records


async def test_model_key_preserves_callback_identity_for_components():
    called_good_trigger = idom.Ref(False)
    good_handler = StaticEventHandler()
    bad_handler = StaticEventHandler()

    @idom.component
    def RootComponent():
        reverse_children, set_reverse_children = use_toggle()

        children = [Trigger(set_reverse_children, key=name) for name in ["good", "bad"]]

        if reverse_children:
            children.reverse()

        return idom.html.div(children)

    @idom.component
    def Trigger(set_reverse_children, key):
        if key == "good":

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
        await render_json_patch(layout)
        for _ in range(3):
            event = LayoutEvent(good_handler.target, [])
            await layout.deliver(event)

            assert called_good_trigger.current
            # reset after checking
            called_good_trigger.current = False

            await render_json_patch(layout)


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
                    "value": [{"children": ["hello"], "tagName": "div"}],
                },
                {"op": "add", "path": "/tagName", "value": "div"},
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
        return idom.html.div(Inner(key=k) for k in items)

    @idom.component
    def Inner(key):
        if key not in registered_finalizers:
            hook = idom.hooks.current_hook()
            finalize(hook, lambda: garbage_collect_items.append(key))
            registered_finalizers.add(key)
        return idom.html.div(key)

    with idom.Layout(Outer()) as layout:
        await render_json_patch(layout)

        pop_item.current()
        await render_json_patch(layout)
        assert garbage_collect_items == [3]

        pop_item.current()
        await render_json_patch(layout)
        assert garbage_collect_items == [3, 2]

        pop_item.current()
        await render_json_patch(layout)
        assert garbage_collect_items == [3, 2, 1]


async def test_duplicate_sibling_keys_causes_error(caplog):
    @idom.component
    def ComponentReturnsDuplicateKeys():
        return idom.html.div(
            idom.html.div(key="duplicate"), idom.html.div(key="duplicate")
        )

    with idom.Layout(ComponentReturnsDuplicateKeys()) as layout:
        await render_json_patch(layout)

    with pytest.raises(ValueError, match=r"Duplicate keys \['duplicate'\] at '/'"):
        raise next(iter(caplog.records)).exc_info[1]


async def test_keyed_components_preserve_hook_on_parent_update():
    outer_hook = HookCatcher()
    inner_hook = HookCatcher()

    @idom.component
    @outer_hook.capture
    def Outer():
        return Inner(key=1)

    @idom.component
    @inner_hook.capture
    def Inner(key):
        return idom.html.div(key)

    with idom.Layout(Outer()) as layout:
        await render_json_patch(layout)
        old_inner_hook = inner_hook.latest

        outer_hook.latest.schedule_render()
        await render_json_patch(layout)
        assert old_inner_hook is inner_hook.latest


async def test_log_error_on_bad_event_handler(caplog):
    bad_handler = StaticEventHandler()

    @idom.component
    def ComponentWithBadEventHandler():
        @bad_handler.use
        def raise_error():
            raise Exception("bad event handler")

        return idom.html.button({"onClick": raise_error})

    with idom.Layout(ComponentWithBadEventHandler()) as layout:
        await render_json_patch(layout)
        event = LayoutEvent(bad_handler.target, [])
        await layout.deliver(event)

    assert next(iter(caplog.records)).message.startswith(
        "Failed to execute event handler"
    )


async def test_schedule_render_from_unmounted_hook(caplog):
    parent_set_state = idom.Ref()

    @idom.component
    def Parent():
        state, parent_set_state.current = idom.hooks.use_state(1)
        return Child(key=state)

    child_hook = HookCatcher()

    @idom.component
    @child_hook.capture
    def Child(key):
        idom.hooks.use_effect(lambda: lambda: print("unmount", key))
        return idom.html.div(key)

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

    assert re.match(
        (
            "Did not render component with model state ID .*? - component already "
            "unmounted or does not belong to this layout"
        ),
        caplog.records[0].message,
    )


async def test_layout_element_cannot_become_a_component(caplog):
    set_child_type = idom.Ref()

    @idom.component
    def Root():
        child_type, set_child_type.current = idom.hooks.use_state("element")
        return idom.html.div(child_nodes[child_type])

    @idom.component
    def Child(key):
        return idom.html.div()

    child_nodes = {
        "element": idom.html.div(key="the-same-key"),
        "component": Child(key="the-same-key"),
    }

    with idom.Layout(Root()) as layout:
        await layout.render()

        set_child_type.current("component")

        await layout.render()

    error = caplog.records[0].exc_info[1]
    assert "prior element with this key wasn't a component" in str(error)


async def test_layout_component_cannot_become_an_element(caplog):
    set_child_type = idom.Ref()

    @idom.component
    def Root():
        child_type, set_child_type.current = idom.hooks.use_state("component")
        return idom.html.div(child_nodes[child_type])

    @idom.component
    def Child(key):
        return idom.html.div()

    child_nodes = {
        "element": idom.html.div(key="the-same-key"),
        "component": Child(key="the-same-key"),
    }

    with idom.Layout(Root()) as layout:
        await layout.render()

        set_child_type.current("element")

        await layout.render()

    error = caplog.records[0].exc_info[1]
    assert "prior element with this key was a component" in str(error)
