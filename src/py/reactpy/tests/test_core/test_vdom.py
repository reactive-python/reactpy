import sys

import pytest
from fastjsonschema import JsonSchemaException

import reactpy
from reactpy.config import REACTPY_DEBUG_MODE
from reactpy.core.events import EventHandler
from reactpy.core.types import VdomDict
from reactpy.core.vdom import is_vdom, make_vdom_constructor, validate_vdom_json

FAKE_EVENT_HANDLER = EventHandler(lambda data: None)
FAKE_EVENT_HANDLER_DICT = {"on_event": FAKE_EVENT_HANDLER}


@pytest.mark.parametrize(
    "result, value",
    [
        (False, {}),
        (False, {"tagName": None}),
        (False, VdomDict()),
        (True, {"tagName": ""}),
        (True, VdomDict(tagName="")),
    ],
)
def test_is_vdom(result, value):
    assert is_vdom(value) == result


@pytest.mark.parametrize(
    "actual, expected",
    [
        (
            reactpy.vdom("div", [reactpy.vdom("div")]),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ),
        (
            reactpy.vdom("div", {"style": {"backgroundColor": "red"}}),
            {"tagName": "div", "attributes": {"style": {"backgroundColor": "red"}}},
        ),
        (
            # multiple iterables of children are merged
            reactpy.vdom("div", [reactpy.vdom("div"), 1], (reactpy.vdom("div"), 2)),
            {
                "tagName": "div",
                "children": [{"tagName": "div"}, 1, {"tagName": "div"}, 2],
            },
        ),
        (
            reactpy.vdom("div", {"on_event": FAKE_EVENT_HANDLER}),
            {"tagName": "div", "eventHandlers": FAKE_EVENT_HANDLER_DICT},
        ),
        (
            reactpy.vdom("div", reactpy.html.h1("hello"), reactpy.html.h2("world")),
            {
                "tagName": "div",
                "children": [
                    {"tagName": "h1", "children": ["hello"]},
                    {"tagName": "h2", "children": ["world"]},
                ],
            },
        ),
        (
            reactpy.vdom("div", {"tagName": "div"}),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ),
        (
            reactpy.vdom("div", (i for i in range(3))),
            {"tagName": "div", "children": [0, 1, 2]},
        ),
        (
            reactpy.vdom("div", (x**2 for x in [1, 2, 3])),
            {"tagName": "div", "children": [1, 4, 9]},
        ),
    ],
)
def test_simple_node_construction(actual, expected):
    assert actual == expected


async def test_callable_attributes_are_cast_to_event_handlers():
    params_from_calls = []

    node = reactpy.vdom(
        "div", {"on_event": lambda *args: params_from_calls.append(args)}
    )

    event_handlers = node.pop("eventHandlers")
    assert node == {"tagName": "div"}

    handler = event_handlers["on_event"]
    assert event_handlers == {"on_event": EventHandler(handler.function)}

    await handler.function([1, 2])
    await handler.function([3, 4, 5])
    assert params_from_calls == [(1, 2), (3, 4, 5)]


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


@pytest.mark.parametrize(
    "value",
    [
        {
            "tagName": "div",
            "children": [
                "Some text",
                {"tagName": "div"},
            ],
        },
        {
            "tagName": "div",
            "attributes": {"style": {"color": "blue"}},
        },
        {
            "tagName": "div",
            "eventHandler": {"target": "something"},
        },
        {
            "tagName": "div",
            "eventHandler": {
                "target": "something",
                "preventDefault": False,
                "stopPropagation": True,
            },
        },
        {
            "tagName": "div",
            "importSource": {"source": "something"},
        },
        {
            "tagName": "div",
            "importSource": {"source": "something", "fallback": None},
        },
        {
            "tagName": "div",
            "importSource": {"source": "something", "fallback": "loading..."},
        },
        {
            "tagName": "div",
            "importSource": {"source": "something", "fallback": {"tagName": "div"}},
        },
        {
            "tagName": "div",
            "children": [
                "Some text",
                {"tagName": "div"},
            ],
            "attributes": {"style": {"color": "blue"}},
            "eventHandler": {
                "target": "something",
                "preventDefault": False,
                "stopPropagation": True,
            },
            "importSource": {
                "source": "something",
                "fallback": {"tagName": "div"},
            },
        },
    ],
)
def test_valid_vdom(value):
    validate_vdom_json(value)


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="error messages are different in Python<3.10"
)
@pytest.mark.parametrize(
    "value, error_message_pattern",
    [
        (
            None,
            r"data must be object",
        ),
        (
            {},
            r"data must contain \['tagName'\] properties",
        ),
        (
            {"tagName": 0},
            r"data\.tagName must be string",
        ),
        (
            {"tagName": "tag", "children": None},
            r"data\.children must be array",
        ),
        (
            {"tagName": "tag", "children": [None]},
            r"data\.children\[0\] must be object or string",
        ),
        (
            {"tagName": "tag", "children": [{"tagName": None}]},
            r"data\.children\[0\]\.tagName must be string",
        ),
        (
            {"tagName": "tag", "attributes": None},
            r"data\.attributes must be object",
        ),
        (
            {"tagName": "tag", "eventHandlers": None},
            r"data\.eventHandlers must be object",
        ),
        (
            {"tagName": "tag", "eventHandlers": {"on_event": None}},
            r"data\.eventHandlers\.on_event must be object",
        ),
        (
            {
                "tagName": "tag",
                "eventHandlers": {"on_event": {}},
            },
            r"data\.eventHandlers\.on_event\ must contain \['target'\] properties",
        ),
        (
            {
                "tagName": "tag",
                "eventHandlers": {
                    "on_event": {
                        "target": "something",
                        "preventDefault": None,
                    }
                },
            },
            r"data\.eventHandlers\.on_event\.preventDefault must be boolean",
        ),
        (
            {
                "tagName": "tag",
                "eventHandlers": {
                    "on_event": {
                        "target": "something",
                        "stopPropagation": None,
                    }
                },
            },
            r"data\.eventHandlers\.on_event\.stopPropagation must be boolean",
        ),
        (
            {"tagName": "tag", "importSource": None},
            r"data\.importSource must be object",
        ),
        (
            {"tagName": "tag", "importSource": {}},
            r"data\.importSource must contain \['source'\] properties",
        ),
        (
            {
                "tagName": "tag",
                "importSource": {"source": "something", "fallback": 0},
            },
            r"data\.importSource\.fallback must be object or string or null",
        ),
        (
            {
                "tagName": "tag",
                "importSource": {"source": "something", "fallback": {"tagName": None}},
            },
            r"data\.importSource\.fallback\.tagName must be string",
        ),
    ],
)
def test_invalid_vdom(value, error_message_pattern):
    with pytest.raises(JsonSchemaException, match=error_message_pattern):
        validate_vdom_json(value)


@pytest.mark.skipif(not REACTPY_DEBUG_MODE.current, reason="Only warns in debug mode")
def test_warn_cannot_verify_keypath_for_genereators():
    with pytest.warns(UserWarning) as record:
        reactpy.vdom("div", (1 for i in range(10)))
        assert len(record) == 1
        assert (
            record[0]
            .message.args[0]
            .startswith("Did not verify key-path integrity of children in generator")
        )


@pytest.mark.skipif(not REACTPY_DEBUG_MODE.current, reason="Only warns in debug mode")
def test_warn_dynamic_children_must_have_keys():
    with pytest.warns(UserWarning) as record:
        reactpy.vdom("div", [reactpy.vdom("div")])
        assert len(record) == 1
        assert record[0].message.args[0].startswith("Key not specified for child")

    @reactpy.component
    def MyComponent():
        return reactpy.vdom("div")

    with pytest.warns(UserWarning) as record:
        reactpy.vdom("div", [MyComponent()])
        assert len(record) == 1
        assert record[0].message.args[0].startswith("Key not specified for child")


@pytest.mark.skipif(not REACTPY_DEBUG_MODE.current, reason="only checked in debug mode")
def test_raise_for_non_json_attrs():
    with pytest.raises(TypeError, match="JSON serializable"):
        reactpy.html.div({"non_json_serializable_object": object()})
