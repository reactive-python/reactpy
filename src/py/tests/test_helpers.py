import pytest

import idom
from idom.helpers import EventHandler, node_constructor


@pytest.mark.parametrize(
    "actual, expected",
    [
        (
            idom.nodes.div(idom.nodes.div()),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ),
        (
            # lists and tuples passed to children are flattened
            idom.nodes.div([idom.nodes.div(), 1], (idom.nodes.div(), 2)),
            {
                "tagName": "div",
                "children": [{"tagName": "div"}, 1, {"tagName": "div"}, 2],
            },
        ),
        (
            # keywords become attributes
            idom.nodes.div(style={"backgroundColor": "blue"}),
            {"tagName": "div", "attributes": {"style": {"backgroundColor": "blue"}}},
        ),
        (
            # eventHandlers is popped from attributes and made a top level field
            idom.nodes.div(eventHandlers=idom.Events()),
            {"tagName": "div", "eventHandlers": idom.Events()},
        ),
    ],
)
def test_simple_node_construction(actual, expected):
    assert actual == expected


def test_node_constructor_factory():
    elmt = node_constructor("some-tag")

    assert elmt(elmt(), data=1) == {
        "tagName": "some-tag",
        "children": [{"tagName": "some-tag"}],
        "attributes": {"data": 1},
    }

    no_children = node_constructor("no-children", allow_children=False)

    with pytest.raises(TypeError):
        no_children(1, 2, 3)

    assert no_children() == {"tagName": "no-children"}


def test_simple_events():
    events = idom.Events()

    @events.on("Click")
    def click_handler():
        pass

    @events.on("keyPress")
    def key_press_handler():
        pass

    assert events == {"onClick": click_handler, "onKeyPress": key_press_handler}

    assert isinstance(events["onClick"], EventHandler)
    assert isinstance(events["onKeyPress"], EventHandler)


def test_event_handler_serialization():
    def handler(key, value):
        return (key, value)

    event_handler = EventHandler(handler, "onKeyPress", "value=target.value", "uuid")
    assert event_handler.serialize() == "uuid_onKeyPress_key;target.value"


async def test_event_handler_props_to_params_mapping():
    def handler(key, value):
        return (key, value)

    event_handler = EventHandler(handler, "onKeyPress", "value=target.value")

    assert await event_handler({"key": 1, "target.value": 2}) == (1, 2)


def test_event_handler_variable_arguments_are_illegal():
    def handler(*args):
        pass

    with pytest.raises(TypeError):
        EventHandler(handler, "event")

    def handler(**kwargs):
        pass

    with pytest.raises(TypeError):
        EventHandler(handler, "event")


def test_var_equivalence():
    r1 = idom.Var([1, 2, 3])
    r2 = idom.Var([1, 2, 3])
    assert r1 == r2


def test_var_set():
    v = idom.Var()
    old_1 = v.set("new_1")
    assert old_1 is idom.Var.empty
    old_2 = v.set("new_2")
    assert old_2 == "new_1"


def test_var_get():
    v = idom.Var()
    assert v.get() is idom.Var.empty
    v.set(1)
    assert v.get() == 1
