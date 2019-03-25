import idom

from .utils import RenderHistory


async def test_simple_layout():
    @idom.element
    def simple_element(self, tag):
        return idom.node(tag)

    element = simple_element("div")
    layout = idom.Layout(element)

    roots, new, old = await layout.render()
    assert roots == [element.id]
    assert new == {element.id: {"tagName": "div"}}
    assert old == []

    element.update("table")

    roots, new, old = await layout.render()
    assert roots == [element.id]
    assert new == {element.id: {"tagName": "table"}}
    assert old == []


async def test_nested_element_layout():

    history = RenderHistory()

    @history.track("parent")
    @idom.element
    def parent_element(self):
        return idom.nodes.div(child_element())

    @history.track("child")
    @idom.element
    def child_element(self):
        return idom.nodes.div()

    layout = idom.Layout(parent_element())

    roots, new, old = await layout.render()

    assert roots == [history.parent_1.id]
    assert new == {
        history.parent_1.id: {
            "tagName": "div",
            "children": [{"data": history.child_1.id, "type": "ref"}],
        },
        history.child_1.id: {"tagName": "div"},
    }
    assert old == []

    history.parent_1.update()

    roots, new, old = await layout.render()

    assert roots == [history.parent_1.id]
    assert new == {
        history.parent_1.id: {
            "tagName": "div",
            "children": [{"data": history.child_2.id, "type": "ref"}],
        },
        history.child_2.id: {"tagName": "div"},
    }
    assert old == [history.child_1.id]
