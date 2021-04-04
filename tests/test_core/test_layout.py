import asyncio
import gc
import re
from weakref import finalize

import pytest

import idom
from idom.core.layout import LayoutEvent, LayoutUpdate
from tests.general_utils import HookCatcher, assert_same_items


def test_layout_update_create_from_apply_to():
    update = LayoutUpdate.create_from({"a": 1, "b": [1]}, {"a": 2, "b": [1, 2]})
    assert update.apply_to({"a": 1, "b": [1]}) == {"a": 2, "b": [1, 2]}


def test_layout_repr():
    @idom.component
    def MyComponent():
        ...

    my_component = MyComponent()
    layout = idom.Layout(my_component)
    assert str(layout) == f"Layout(MyComponent({hex(id(my_component))}))"


def test_layout_expects_abstract_component():
    with pytest.raises(TypeError, match="Expected an AbstractComponent"):
        idom.Layout(None)
    with pytest.raises(TypeError, match="Expected an AbstractComponent"):
        idom.Layout(idom.html.div())


def test_not_open_layout_update_logs_error(caplog):
    @idom.component
    def Component():
        ...

    component = Component()
    layout = idom.Layout(component)
    layout.update(component)

    assert re.match(
        "Did not update .*? - resources of .*? are closed",
        next(iter(caplog.records)).msg,
    )


async def test_simple_layout():
    set_state_hook = idom.Ref(None)

    @idom.component
    def SimpleComponent():
        tag, set_state_hook.current = idom.hooks.use_state("div")
        return idom.vdom(tag)

    async with idom.Layout(SimpleComponent()) as layout:
        path, changes = await layout.render()

        assert path == ""
        assert changes == [{"op": "add", "path": "/tagName", "value": "div"}]

        set_state_hook.current("table")
        path, changes = await layout.render()

        assert path == ""
        assert changes == [{"op": "replace", "path": "/tagName", "value": "table"}]


async def test_nested_component_layout():
    parent_set_state = idom.Ref(None)
    child_set_state = idom.Ref(None)

    @idom.component
    def Parent():
        state, parent_set_state.current = idom.hooks.use_state(0)
        return idom.html.div(state, Child())

    @idom.component
    def Child():
        state, child_set_state.current = idom.hooks.use_state(0)
        return idom.html.div(state)

    async with idom.Layout(Parent()) as layout:

        path, changes = await layout.render()

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
        path, changes = await layout.render()

        assert path == ""
        assert changes == [{"op": "replace", "path": "/children/0", "value": "1"}]

        child_set_state.current(1)
        path, changes = await layout.render()

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

    async with idom.Layout(Main()) as layout:
        patch = await layout.render()
        assert_same_items(
            patch.changes,
            [
                {
                    "op": "add",
                    "path": "/children",
                    "value": [
                        {"tagName": "div", "children": ["hello"]},
                        {"tagName": "div", "__error__": "Something went wrong :("},
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

    async with idom.Layout(Main()) as layout:
        patch = await layout.render()
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

    @idom.component
    @outer_component_hook.capture
    def Outer():
        component = idom.hooks.current_hook().component
        live_components.add(id(component))
        finalize(component, live_components.remove, id(component))
        return Inner()

    @idom.component
    def Inner():
        component = idom.hooks.current_hook().component
        live_components.add(id(component))
        finalize(component, live_components.remove, id(component))
        return idom.html.div()

    async with idom.Layout(Outer()) as layout:
        await layout.render()

        assert len(live_components) == 2

        last_live_components = live_components.copy()
        # The existing `Outer` component rerenders. A new `Inner` component is created and
        # the the old `Inner` component should be deleted. Thus there should be one
        # changed component in the set of `live_components` the old `Inner` deleted and new
        # `Inner` added.
        outer_component_hook.schedule_render()
        await layout.render()

        assert len(live_components - last_live_components) == 1

    # The layout still holds a reference to the root so that's
    # only deleted once we release a reference to it.
    del layout
    # the hook also contains a reference to the root component
    del outer_component_hook

    gc.collect()
    assert not live_components


async def test_double_updated_component_is_not_double_rendered():
    hook = HookCatcher()
    run_count = idom.Ref(0)

    @idom.component
    @hook.capture
    def AnyComponent():
        run_count.current += 1
        return idom.html.div()

    async with idom.Layout(AnyComponent()) as layout:
        await layout.render()

        assert run_count.current == 1

        hook.schedule_render()
        hook.schedule_render()

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

    async with idom.Layout(Parent()) as layout:
        await layout.render()

        hook.current.schedule_render()

        update = await layout.render()
        assert update.path == "/children/0/children/0"


async def test_log_on_dispatch_to_missing_event_handler(caplog):
    @idom.component
    def SomeComponent():
        return idom.html.div()

    async with idom.Layout(SomeComponent()) as layout:
        await layout.dispatch(LayoutEvent(target="missing", data=[]))

    assert re.match(
        "Ignored event - handler 'missing' does not exist or its component unmounted",
        next(iter(caplog.records)).msg,
    )


def use_toggle(init=False):
    state, set_state = idom.hooks.use_state(init)
    return state, lambda: set_state(lambda old: not old)


async def test_model_key_preserves_callback_identity_for_common_elements():
    called_good_trigger = idom.Ref(False)

    @idom.component
    def MyComponent():
        reverse_children, set_reverse_children = use_toggle()

        def good_trigger():
            called_good_trigger.current = True
            set_reverse_children()

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

    async with idom.Layout(MyComponent(key="component")) as layout:
        await layout.render()
        for i in range(3):
            event = LayoutEvent("/component/good/onClick", [])
            await layout.dispatch(event)

            assert called_good_trigger.current
            # reset after checking
            called_good_trigger.current = False

            await layout.render()


async def test_model_key_preserves_callback_identity_for_components():
    called_good_trigger = idom.Ref(False)

    @idom.component
    def RootComponent():
        reverse_children, set_reverse_children = use_toggle()

        children = [
            Trigger(name, set_reverse_children, key=name) for name in ["good", "bad"]
        ]

        if reverse_children:
            children.reverse()

        return idom.html.div(children)

    @idom.component
    def Trigger(name, set_reverse_children):
        def callback():
            if name == "good":
                called_good_trigger.current = True
                set_reverse_children()
            else:
                raise ValueError("Called bad trigger")

        return idom.html.button({"onClick": callback, "id": "good"}, "good")

    async with idom.Layout(RootComponent(key="root")) as layout:
        await layout.render()
        for i in range(3):
            event = LayoutEvent("/root/good/onClick", [])
            await layout.dispatch(event)

            assert called_good_trigger.current
            # reset after checking
            called_good_trigger.current = False

            await layout.render()
