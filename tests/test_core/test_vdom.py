import sys

import pytest
from fastjsonschema import JsonSchemaException

import reactpy
from reactpy.config import REACTPY_DEBUG
from reactpy.core.events import EventHandler
from reactpy.core.vdom import Vdom, is_vdom, validate_vdom_json
from reactpy.types import VdomDict, VdomTypeDict

FAKE_EVENT_HANDLER = EventHandler(lambda data: None)
FAKE_EVENT_HANDLER_DICT = {"onEvent": FAKE_EVENT_HANDLER}


@pytest.mark.parametrize(
    "result, value",
    [
        (False, {}),
        (False, {"tagName": None}),
        (False, {"tagName": ""}),
        (False, VdomTypeDict(tagName="div")),
        (True, VdomDict(tagName="")),
        (True, VdomDict(tagName="div")),
    ],
)
def test_is_vdom(result, value):
    assert result == is_vdom(value)


@pytest.mark.parametrize(
    "actual, expected",
    [
        (
            reactpy.Vdom("div")([reactpy.Vdom("div")()]),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ),
        (
            reactpy.Vdom("div")({"style": {"backgroundColor": "red"}}),
            {"tagName": "div", "attributes": {"style": {"backgroundColor": "red"}}},
        ),
        (
            # multiple iterables of children are merged
            reactpy.Vdom("div")(
                (
                    [reactpy.Vdom("div")(), 1],
                    (reactpy.Vdom("div")(), 2),
                )
            ),
            {
                "tagName": "div",
                "children": [{"tagName": "div"}, 1, {"tagName": "div"}, 2],
            },
        ),
        (
            reactpy.Vdom("div")({"onEvent": FAKE_EVENT_HANDLER}),
            {"tagName": "div", "eventHandlers": FAKE_EVENT_HANDLER_DICT},
        ),
        (
            reactpy.Vdom("div")((reactpy.html.h1("hello"), reactpy.html.h2("world"))),
            {
                "tagName": "div",
                "children": [
                    {"tagName": "h1", "children": ["hello"]},
                    {"tagName": "h2", "children": ["world"]},
                ],
            },
        ),
        (
            reactpy.Vdom("div")({"tagName": "div"}),
            {"tagName": "div", "attributes": {"tagName": "div"}},
        ),
        (
            reactpy.Vdom("div")((i for i in range(3))),
            {"tagName": "div", "children": [0, 1, 2]},
        ),
        (
            reactpy.Vdom("div")((x**2 for x in [1, 2, 3])),
            {"tagName": "div", "children": [1, 4, 9]},
        ),
        (
            reactpy.Vdom("div")(["child_1", ["child_2"]]),
            {"tagName": "div", "children": ["child_1", "child_2"]},
        ),
    ],
)
def test_simple_node_construction(actual, expected):
    assert actual == expected


async def test_callable_attributes_are_cast_to_event_handlers():
    params_from_calls = []

    node = reactpy.Vdom("div")(
        {"onEvent": lambda *args: params_from_calls.append(args)}
    )

    event_handlers = node.pop("eventHandlers")
    assert node == {"tagName": "div"}

    handler = event_handlers["onEvent"]
    assert event_handlers == {"onEvent": EventHandler(handler.function)}

    await handler.function([1, 2])
    await handler.function([3, 4, 5])
    assert params_from_calls == [(1, 2), (3, 4, 5)]


def test_make_vdom_constructor():
    elmt = Vdom("some-tag")

    assert elmt({"data": 1}, [elmt()]) == {
        "tagName": "some-tag",
        "children": [{"tagName": "some-tag"}],
        "attributes": {"data": 1},
    }

    no_children = Vdom("no-children", allow_children=False)

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
            {"tagName": "tag", "eventHandlers": {"onEvent": None}},
            r"data\.eventHandlers\.onEvent must be object",
        ),
        (
            {
                "tagName": "tag",
                "eventHandlers": {"onEvent": {}},
            },
            r"data\.eventHandlers\.onEvent\ must contain \['target'\] properties",
        ),
        (
            {
                "tagName": "tag",
                "eventHandlers": {
                    "onEvent": {
                        "target": "something",
                        "preventDefault": None,
                    }
                },
            },
            r"data\.eventHandlers\.onEvent\.preventDefault must be boolean",
        ),
        (
            {
                "tagName": "tag",
                "eventHandlers": {
                    "onEvent": {
                        "target": "something",
                        "stopPropagation": None,
                    }
                },
            },
            r"data\.eventHandlers\.onEvent\.stopPropagation must be boolean",
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


@pytest.mark.skipif(not REACTPY_DEBUG.current, reason="Only warns in debug mode")
def test_warn_cannot_verify_keypath_for_genereators():
    with pytest.warns(UserWarning) as record:
        reactpy.Vdom("div")((1 for i in range(10)))
        assert len(record) == 1
        assert (
            record[0]
            .message.args[0]
            .startswith("Did not verify key-path integrity of children in generator")
        )


@pytest.mark.skipif(not REACTPY_DEBUG.current, reason="Only warns in debug mode")
def test_warn_dynamic_children_must_have_keys():
    with pytest.warns(UserWarning) as record:
        reactpy.Vdom("div")([reactpy.Vdom("div")()])
        assert len(record) == 1
        assert record[0].message.args[0].startswith("Key not specified for child")

    @reactpy.component
    def MyComponent():
        return reactpy.Vdom("div")()

    with pytest.warns(UserWarning) as record:
        reactpy.Vdom("div")([MyComponent()])
        assert len(record) == 1
        assert record[0].message.args[0].startswith("Key not specified for child")


@pytest.mark.skipif(not REACTPY_DEBUG.current, reason="only checked in debug mode")
def test_raise_for_non_json_attrs():
    with pytest.raises(TypeError, match="JSON serializable"):
        reactpy.html.div({"nonJsonSerializableObject": object()})


def test_invalid_vdom_keys():
    with pytest.raises(ValueError, match="Invalid keys:*"):
        reactpy.types.VdomDict(tagName="test", foo="bar")

    with pytest.raises(KeyError, match="Invalid key:*"):
        reactpy.types.VdomDict(tagName="test")["foo"] = "bar"

    with pytest.raises(ValueError, match="VdomDict requires a 'tagName' key."):
        reactpy.types.VdomDict(foo="bar")
