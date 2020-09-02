import gc
from weakref import finalize

import pytest

import idom
from idom.core.layout import LayoutUpdate

from tests.general_utils import assert_unordered_equal

from .utils import HookCatcher


def test_layout_repr():
    @idom.element
    async def MyElement():
        ...

    my_element = MyElement()
    layout = idom.Layout(my_element)
    assert str(layout) == f"Layout(MyElement({my_element.id}))"


def test_layout_expects_abstract_element():
    with pytest.raises(TypeError, match="Expected an AbstractElement"):
        idom.Layout(None)
    with pytest.raises(TypeError, match="Expected an AbstractElement"):
        idom.Layout(idom.html.div())


async def test_simple_layout():
    set_state_hook = idom.Ref(None)

    @idom.element
    async def SimpleElement():
        tag, set_state_hook.current = idom.hooks.use_state("div")
        return idom.vdom(tag)

    async with idom.Layout(SimpleElement()) as layout:
        path, changes = await layout.render()

        assert path == ""
        assert_unordered_equal(
            changes,
            [
                {"op": "add", "path": "/eventHandlers", "value": {}},
                {"op": "add", "path": "/tagName", "value": "div"},
            ],
        )

        set_state_hook.current("table")
        path, changes = await layout.render()

        assert path == ""
        assert changes == [{"op": "replace", "path": "/tagName", "value": "table"}]


async def test_nested_element_layout():
    parent_set_state = idom.Ref(None)
    child_set_state = idom.Ref(None)

    @idom.element
    async def Parent():
        state, parent_set_state.current = idom.hooks.use_state(0)
        return idom.html.div(state, Child())

    @idom.element
    async def Child():
        state, child_set_state.current = idom.hooks.use_state(0)
        return idom.html.div(state)

    async with idom.Layout(Parent()) as layout:

        path, changes = await layout.render()

        assert path == ""
        assert_unordered_equal(
            changes,
            [
                {"op": "add", "path": "/tagName", "value": "div"},
                {
                    "op": "add",
                    "path": "/children",
                    "value": [
                        "0",
                        {"children": ["0"], "eventHandlers": {}, "tagName": "div"},
                    ],
                },
                {"op": "add", "path": "/eventHandlers", "value": {}},
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
    history = RenderHistory()

    @history.track("main")
    @idom.element
    async def Main():
        return idom.html.div([OkChild(), BadChild(), OkChild()])

    @history.track("ok_child")
    @idom.element
    async def OkChild():
        return idom.html.div(["hello"])

    @history.track("bad_child")
    @idom.element
    async def BadChild():
        raise ValueError("Something went wrong :(")

    async with idom.Layout(Main()) as layout:

        src, new, old, errors = await layout.render()

        assert src == history.main_1.id

        assert new == {
            history.main_1.id: {
                "tagName": "div",
                "children": [
                    {"type": "ref", "data": history.ok_child_1.id},
                    {"type": "ref", "data": history.bad_child_1.id},
                    {"type": "ref", "data": history.ok_child_2.id},
                ],
            },
            history.ok_child_1.id: {
                "tagName": "div",
                "children": [{"type": "str", "data": "hello"}],
            },
            history.bad_child_1.id: {"tagName": "div"},
            history.ok_child_2.id: {
                "tagName": "div",
                "children": [{"type": "str", "data": "hello"}],
            },
        }

        assert old == []

        assert len(errors) == 1
        assert isinstance(errors[0], ValueError)
        assert str(errors[0]) == "Something went wrong :("


async def test_render_raw_vdom_dict_with_single_element_object_as_children():
    history = RenderHistory()

    @history.track("main")
    @idom.element
    async def Main():
        return {"tagName": "div", "children": Child()}

    @history.track("child")
    @idom.element
    async def Child():
        return {"tagName": "div", "children": {"tagName": "h1"}}

    async with idom.Layout(Main()) as layout:
        render = await layout.render()

    assert render == LayoutUpdate(
        src=history.main_1.id,
        new={
            history.child_1.id: {
                "tagName": "div",
                "children": [{"type": "obj", "data": {"tagName": "h1"}}],
            },
            history.main_1.id: {
                "tagName": "div",
                "children": [{"type": "ref", "data": history.child_1.id}],
            },
        },
        old=[],
        errors=[],
    )


async def test_elements_are_garbage_collected():
    live_elements = set()

    @idom.element
    async def Outer():
        element = idom.hooks.current_hook().element
        live_elements.add(element.id)
        finalize(element, live_elements.remove, element.id)

        hook = idom.hooks.current_hook()

        @idom.event(target_id="force-update")
        async def force_update():
            hook.schedule_render()

        return idom.html.div({"onEvent": force_update}, Inner())

    @idom.element
    async def Inner():
        element = idom.hooks.current_hook().element
        live_elements.add(element.id)
        finalize(element, live_elements.remove, element.id)
        return idom.html.div()

    async with idom.Layout(Outer()) as layout:
        await layout.render()
        assert len(live_elements) == 2
        last_live_elements = live_elements.copy()
        # The existing `Outer` element rerenders. A new `Inner` element is created and
        # the the old `Inner` element should be deleted. Thus there should be one
        # changed element in the set of `live_elements` the old `Inner` deleted and new
        # `Inner` added.
        await layout.dispatch(idom.core.layout.LayoutEvent("force-update", []))
        await layout.render()
        assert len(live_elements - last_live_elements) == 1

    # The layout still holds a reference to the root so that's
    # only deleted once we release a reference to it.
    del layout
    gc.collect()
    assert not live_elements


def test_double_updated_element_is_not_double_rendered():
    assert False
