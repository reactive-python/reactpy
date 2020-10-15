import asyncio
import gc
import re
from weakref import finalize

import pytest

import idom
from idom.core.layout import LayoutUpdate

from tests.general_utils import assert_same_items, HookCatcher


def test_layout_update_create_from_apply_to():
    update = LayoutUpdate.create_from({"a": 1, "b": [1]}, {"a": 2, "b": [1, 2]})
    assert update.apply_to({"a": 1, "b": [1]}) == {"a": 2, "b": [1, 2]}


def test_layout_repr():
    @idom.element
    def MyElement():
        ...

    my_element = MyElement()
    layout = idom.Layout(my_element)
    assert str(layout) == f"Layout(MyElement({hex(id(my_element))}))"


def test_layout_expects_abstract_element():
    with pytest.raises(TypeError, match="Expected an AbstractElement"):
        idom.Layout(None)
    with pytest.raises(TypeError, match="Expected an AbstractElement"):
        idom.Layout(idom.html.div())


def test_not_open_layout_update_logs_error(caplog):
    @idom.element
    def Element():
        ...

    element = Element()
    layout = idom.Layout(element)
    layout.update(element)

    assert re.match(
        "Did not update .*? - resources of .*? are closed",
        next(iter(caplog.records)).msg,
    )


async def test_simple_layout():
    set_state_hook = idom.Ref(None)

    @idom.element
    def SimpleElement():
        tag, set_state_hook.current = idom.hooks.use_state("div")
        return idom.vdom(tag)

    async with idom.Layout(SimpleElement()) as layout:
        path, changes = await layout.render()

        assert path == ""
        assert changes == [{"op": "add", "path": "/tagName", "value": "div"}]

        set_state_hook.current("table")
        path, changes = await layout.render()

        assert path == ""
        assert changes == [{"op": "replace", "path": "/tagName", "value": "table"}]


async def test_nested_element_layout():
    parent_set_state = idom.Ref(None)
    child_set_state = idom.Ref(None)

    @idom.element
    def Parent():
        state, parent_set_state.current = idom.hooks.use_state(0)
        return idom.html.div(state, Child())

    @idom.element
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
    @idom.element
    def Main():
        return idom.html.div([OkChild(), BadChild(), OkChild()])

    @idom.element
    def OkChild():
        return idom.html.div(["hello"])

    @idom.element
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


async def test_render_raw_vdom_dict_with_single_element_object_as_children():
    @idom.element
    def Main():
        return {"tagName": "div", "children": Child()}

    @idom.element
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


async def test_elements_are_garbage_collected():
    live_elements = set()
    outer_element_hook = HookCatcher()

    @idom.element
    @outer_element_hook.capture
    def Outer():
        element = idom.hooks.current_hook().element
        live_elements.add(id(element))
        finalize(element, live_elements.remove, id(element))

        hook = idom.hooks.current_hook()

        @idom.event(target_id="force-update")
        async def force_update():
            hook.schedule_render()

        return idom.html.div({"onEvent": force_update}, Inner())

    @idom.element
    def Inner():
        element = idom.hooks.current_hook().element
        live_elements.add(id(element))
        finalize(element, live_elements.remove, id(element))
        return idom.html.div()

    async with idom.Layout(Outer()) as layout:
        await layout.render()

        assert len(live_elements) == 2

        last_live_elements = live_elements.copy()
        # The existing `Outer` element rerenders. A new `Inner` element is created and
        # the the old `Inner` element should be deleted. Thus there should be one
        # changed element in the set of `live_elements` the old `Inner` deleted and new
        # `Inner` added.
        outer_element_hook.schedule_render()
        await layout.render()

        assert len(live_elements - last_live_elements) == 1

    # The layout still holds a reference to the root so that's
    # only deleted once we release a reference to it.
    del layout
    # the hook also contains a reference to the root element
    del outer_element_hook

    gc.collect()
    assert not live_elements


async def test_double_updated_element_is_not_double_rendered():
    hook = HookCatcher()
    run_count = idom.Ref(0)

    @idom.element
    @hook.capture
    def AnElement():
        run_count.current += 1
        return idom.html.div()

    async with idom.Layout(AnElement()) as layout:
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


async def test_update_path_to_element_that_is_not_direct_child_is_correct():
    hook = HookCatcher()

    @idom.element
    def Parent():
        return idom.html.div(idom.html.div(Child()))

    @idom.element
    @hook.capture
    def Child():
        return idom.html.div()

    async with idom.Layout(Parent()) as layout:
        await layout.render()

        hook.current.schedule_render()

        update = await layout.render()
        assert update.path == "/children/0/children/0"
