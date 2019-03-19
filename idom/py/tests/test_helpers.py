import pytest

import idom
from idom.helpers import EventHandler


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


@pytest.mark.parametrize(
    "actual, expected",
    [
        (
            idom.node("div", "a-string", key="value"),
            {
                "tagName": "div",
                "children": ["a-string"],
                "eventHandlers": {},
                "attributes": {"style": {}, "key": "value"},
            },
        ),
        (
            idom.node("div", [1, 2, 3], [4, 5, 6]),
            {
                "tagName": "div",
                "children": [1, 2, 3, 4, 5, 6],
                "eventHandlers": {},
                "attributes": {"style": {}},
            },
        ),
    ],
)
def test_node(actual, expected):
    assert actual == expected


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
