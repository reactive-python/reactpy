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
    async def my_element(self):
        ...

    layout = idom.Layout(my_element())
    assert layout.loop is event_loop
    # await the render since creating the layout schedules a render task
    await layout.render()


async def test_simple_layout():
    @idom.element
    async def simple_element(self, tag):
        return idom.vdom(tag)

    element = simple_element("div")
    layout = idom.Layout(element)

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
    async def parent_element(self):
        return idom.html.div([child_element()])

    @history.track("child")
    @idom.element
    async def child_element(self):
        return idom.html.div()

    layout = idom.Layout(parent_element())

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
    async def main(self):
        return idom.html.div([ok_child(), bad_child()])

    @history.track("ok_child")
    @idom.element
    async def ok_child(self):
        return idom.html.div(["hello"])

    @idom.element
    async def bad_child(self):
        raise ValueError("Something went wrong :(")

    layout = idom.Layout(main())

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
    async def main(self):
        return {"tagName": "div", "children": child()}

    @history.track("child")
    @idom.element
    async def child(self):
        return {"tagName": "div", "children": {"tagName": "h1"}}

    render = await idom.Layout(main()).render()

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
    async def main(self):
        return child()

    @history.track("child")
    @idom.element
    async def child(self):
        return idom.html.div()

    layout = idom.Layout(main())
    await layout.render()

    assert layout._element_parent(history.main_1) is None

    @idom.element
    async def element_not_in_layout(self):
        ...

    with pytest.raises(KeyError):
        layout._element_parent(element_not_in_layout())
