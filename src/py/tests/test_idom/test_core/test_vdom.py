import pytest

import idom
from idom.core.vdom import node_constructor


fake_events = idom.Events()


@fake_events.on("Click")
async def handler(event):
    pass


@pytest.mark.parametrize(
    "actual, expected",
    [
        (
            idom.html.div([idom.html.div()]),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ),
        (
            # lists and tuples passed to children are flattened
            idom.html.div([idom.html.div(), 1], (idom.html.div(), 2)),
            {
                "tagName": "div",
                "children": [{"tagName": "div"}, 1, {"tagName": "div"}, 2],
            },
        ),
        (
            # keywords become attributes
            idom.html.div({"style": {"backgroundColor": "blue"}}),
            {"tagName": "div", "attributes": {"style": {"backgroundColor": "blue"}}},
        ),
        (
            idom.html.div(event_handlers=fake_events),
            {"tagName": "div", "eventHandlers": fake_events},
        ),
    ],
)
def test_simple_node_construction(actual, expected):
    print(actual, expected)
    assert actual == expected


def test_node_constructor_factory():
    elmt = node_constructor("some-tag")

    assert elmt([elmt()], {"data": 1}) == {
        "tagName": "some-tag",
        "children": [{"tagName": "some-tag"}],
        "attributes": {"data": 1},
    }

    no_children = node_constructor("no-children", allow_children=False)

    with pytest.raises(TypeError):
        no_children(1, 2, 3)

    assert no_children() == {"tagName": "no-children"}
