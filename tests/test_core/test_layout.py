import gc
import asyncio
from weakref import finalize

import pytest

import idom
from idom.core.layout import LayoutUpdate

from .utils import RenderHistory


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


async def test_layout_has_event_loop(event_loop):
    @idom.element
    async def MyElement():
        return idom.html.div()

    async with idom.Layout(MyElement()) as layout:
        assert layout.loop is event_loop
        # await the render since creating the layout schedules a render task
        await layout.render()


async def test_layout_cancels_renders_on_close():
    event_that_is_never_set = asyncio.Event()
    render_is_cancelled = asyncio.Event()

    @idom.element
    async def MyElement():
        try:
            await event_that_is_never_set.wait()
        finally:
            render_is_cancelled.set()

    async with idom.Layout(MyElement()):
        await asyncio.sleep(0.1)

    await render_is_cancelled.wait()


async def test_simple_layout():
    set_state_hook = idom.Ref(None)

    @idom.element
    async def SimpleElement(tag):
        tag, set_tag = idom.hooks.use_state(tag)
        set_state_hook.current = set_tag
        return idom.vdom(tag)

    element = SimpleElement("div")
    async with idom.Layout(element) as layout:

        src, new, old, errors = await layout.render()
        assert src == element.id
        assert new == {element.id: {"tagName": "div"}}
        assert old == []
        assert errors == []

        set_state_hook.current("table")

        src, new, old, errors = await layout.render()
        assert src == element.id
        assert new == {element.id: {"tagName": "table"}}
        assert old == []
        assert errors == []


async def test_nested_element_layout():

    history = RenderHistory()

    @history.track("parent")
    @idom.element
    async def Parent():
        return idom.html.div([Child()])

    @history.track("child")
    @idom.element
    async def Child():
        return idom.html.div()

    async with idom.Layout(Parent()) as layout:

        src, new, old, errors = await layout.render()

        assert src == history.parent_1.id
        assert new == {
            history.parent_1.id: {
                "tagName": "div",
                "children": [{"data": history.child_1.id, "type": "ref"}],
            },
            history.child_1.id: {"tagName": "div"},
        }
        assert old == []
        assert errors == []

        layout.update(history.parent_1)

        src, new, old, errors = await layout.render()

        assert src == history.parent_1.id
        assert new == {
            history.parent_1.id: {
                "tagName": "div",
                "children": [{"data": history.child_2.id, "type": "ref"}],
            },
            history.child_2.id: {"tagName": "div"},
        }
        assert old == [history.child_1.id]
        assert errors == []


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

        update = idom.hooks.use_update()

        @idom.event(target_id="force-update")
        async def force_update():
            update()

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
