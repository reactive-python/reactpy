import asyncio

import pytest

import idom
from idom.core.layout import LayoutUpdate

from .utils import RenderHistory


def test_layout_expects_abstract_element():
    with pytest.raises(TypeError, match="Expected an AbstractElement"):
        idom.Layout(None)
    with pytest.raises(TypeError, match="Expected an AbstractElement"):
        idom.Layout(idom.html.div())


async def test_layout_has_event_loop(event_loop):
    @idom.element
    async def MyElement(self):
        ...

    async with idom.Layout(MyElement()) as layout:
        assert layout.loop is event_loop
        # await the render since creating the layout schedules a render task
        await layout.render()


async def test_layout_cancels_renders_on_close():
    event_that_is_never_set = asyncio.Event()
    render_is_cancelled = asyncio.Event()

    @idom.element
    async def MyElement(self):
        try:
            await event_that_is_never_set.wait()
        finally:
            render_is_cancelled.set()

    async with idom.Layout(MyElement()):
        await asyncio.sleep(0.1)

    await render_is_cancelled.wait()


async def test_simple_layout():
    @idom.element
    async def SimpleElement(self, tag):
        return idom.vdom(tag)

    element = SimpleElement("div")
    async with idom.Layout(element) as layout:

        src, new, old, error = await layout.render()
        assert src == element.id
        assert new == {element.id: {"tagName": "div"}}
        assert old == []

        element.update("table")

        src, new, old, error = await layout.render()
        assert src == element.id
        assert new == {element.id: {"tagName": "table"}}
        assert old == []


async def test_nested_element_layout():

    history = RenderHistory()

    @history.track("parent")
    @idom.element
    async def Parent(self):
        return idom.html.div([Child()])

    @history.track("child")
    @idom.element
    async def Child(self):
        return idom.html.div()

    async with idom.Layout(Parent()) as layout:

        src, new, old, error = await layout.render()

        assert src == history.parent_1.id
        assert new == {
            history.parent_1.id: {
                "tagName": "div",
                "children": [{"data": history.child_1.id, "type": "ref"}],
            },
            history.child_1.id: {"tagName": "div"},
        }
        assert old == []

        history.parent_1.update()

        src, new, old, error = await layout.render()

        assert src == history.parent_1.id
        assert new == {
            history.parent_1.id: {
                "tagName": "div",
                "children": [{"data": history.child_2.id, "type": "ref"}],
            },
            history.child_2.id: {"tagName": "div"},
        }
        assert old == [history.child_1.id]


async def test_layout_render_error_has_partial_update():
    history = RenderHistory()

    @history.track("main")
    @idom.element
    async def Main(self):
        return idom.html.div([OkChild(), BadChild()])

    @history.track("ok_child")
    @idom.element
    async def OkChild(self):
        return idom.html.div(["hello"])

    @idom.element
    async def BadChild(self):
        raise ValueError("Something went wrong :(")

    async with idom.Layout(Main()) as layout:

        update = await layout.render()
        assert isinstance(update.error, ValueError)

        assert update == LayoutUpdate(
            src=history.main_1.id,
            new={
                history.ok_child_1.id: {
                    "tagName": "div",
                    "children": [{"type": "str", "data": "hello"}],
                }
            },
            old=[],
            error=update.error,
        )


async def test_render_raw_vdom_dict_with_single_element_object_as_children():
    history = RenderHistory()

    @history.track("main")
    @idom.element
    async def Main(self):
        return {"tagName": "div", "children": Child()}

    @history.track("child")
    @idom.element
    async def Child(self):
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
        error=None,
    )


async def test_element_parents_must_exist_unless_is_root():
    history = RenderHistory()

    @history.track("main")
    @idom.element
    async def Main(self):
        return Child()

    @history.track("child")
    @idom.element
    async def Child(self):
        return idom.html.div()

    @idom.element
    async def element_not_in_layout(self):
        ...

    async with idom.Layout(Main()) as layout:
        await layout.render()

        state = layout._element_state

        with pytest.raises(KeyError):
            layout._element_parent(element_not_in_layout())

    assert not state
