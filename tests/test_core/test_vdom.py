import pytest

import idom
from idom.core.vdom import make_vdom_constructor, component


fake_events = idom.Events()


@fake_events.on("Click")
async def handler(event):
    pass


@pytest.mark.parametrize("actual, expected", [(
            idom.vdom("div", [idom.vdom("div")]),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ), (
            idom.vdom("div", {"style": {"backgroundColor": "red"}}),
            {"tagName": "div", "attributes": {"style": {"backgroundColor": "red"}}},
        ), (
            # multiple iterables of children are merged
            idom.vdom("div", [idom.vdom("div"), 1], (idom.vdom("div"), 2)),
            {
                "tagName": "div",
                "children": [{"tagName": "div"}, 1, {"tagName": "div"}, 2],
            },
        ), (
            # multiple dictionaries of attributes are merged
            idom.vdom("div", {"width": "30px"}, {"height": "20px"}),
            {"tagName": "div", "attributes": {"width": "30px", "height": "20px"}},
        ), (
            idom.vdom(
                "div",
                {"width": "30px"},
                {"height": "20px"},
                [idom.vdom("div"), 1],
                (idom.vdom("div"), 2),
            ),
            {
                "tagName": "div",
                "children": [{"tagName": "div"}, 1, {"tagName": "div"}, 2],
                "attributes": {"width": "30px", "height": "20px"},
            },
        ), (
            idom.vdom("div", event_handlers=fake_events),
            {"tagName": "div", "eventHandlers": fake_events},
        ), (
            idom.vdom("div", idom.html.h1("hello"), idom.html.h2("world")),
            {
                "tagName": "div",
                "children": [
                    {"tagName": "h1", "children": ["hello"]},
                    {"tagName": "h2", "children": ["world"]},
                ],
            },
        ), (
            idom.vdom("div", {"tagName": "div"}),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ), (idom.vdom("div", iter(range(3))), {"tagName": "div", "children": [0, 1, 2]}), (
            idom.vdom("div", map(lambda x: x ** 2, [1, 2, 3])),
            {"tagName": "div", "children": [1, 4, 9]},
        )])
def test_simple_node_construction(actual, expected):
    assert actual == expected


def test_vdom_attribute_arguments_come_before_children():
    with pytest.raises(ValueError):
        idom.vdom("div", ["c1", "c2"], {"attr": 1})


def test_make_vdom_constructor():
    elmt = make_vdom_constructor("some-tag")

    assert elmt({"data": 1}, [elmt()]) == {
        "tagName": "some-tag",
        "children": [{"tagName": "some-tag"}],
        "attributes": {"data": 1},
    }

    no_children = make_vdom_constructor("no-children", allow_children=False)

    with pytest.raises(TypeError, match="cannot have children"):
        no_children([1, 2, 3])

    assert no_children() == {"tagName": "no-children"}


def test_vdom_component():
    def MyComponentWithAttributes(x, y):
        return idom.html.div({"x": x * 2, "y": y * 2})

    assert component(MyComponentWithAttributes, {"x": 1}, {"y": 2}) == {
        "tagName": "div",
        "attributes": {"x": 2, "y": 4},
    }

    with pytest.raises(TypeError, match="unexpected keyword argument 'children'"):
        assert component(MyComponentWithAttributes, "a-child")

    def MyComponentWithChildren(children):
        return idom.html.div(children + ["world"])

    assert component(MyComponentWithChildren, "hello") == {
        "tagName": "div",
        "children": ["hello", "world"],
    }

    with pytest.raises(TypeError, match="unexpected keyword argument"):
        assert component(MyComponentWithAttributes, {"an-attribute": 1})

    def MyComponentWithChildrenAndAttributes(children, x):
        return idom.html.div({"x": x * 2}, children + ["world"])

    assert component(MyComponentWithChildrenAndAttributes, {"x": 2}, "hello") == {
        "tagName": "div",
        "attributes": {"x": 4},
        "children": ["hello", "world"],
    }
