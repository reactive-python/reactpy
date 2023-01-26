import sys

import pytest
from fastjsonschema import JsonSchemaException

import idom
from idom.config import IDOM_DEBUG_MODE
from idom.core.events import EventHandler
from idom.core.types import VdomDict
from idom.core.vdom import (
    is_vdom,
    make_vdom_constructor,
    validate_vdom_json,
    with_import_source,
)


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
            idom.vdom("div", [idom.vdom("div")]),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ),
        (
            idom.vdom("div", style={"backgroundColor": "red"}),
            {"tagName": "div", "attributes": {"style": {"backgroundColor": "red"}}},
        ),
        (
            # multiple iterables of children are merged
            idom.vdom("div", [idom.vdom("div"), 1], (idom.vdom("div"), 2)),
            {
                "tagName": "div",
                "children": [{"tagName": "div"}, 1, {"tagName": "div"}, 2],
            },
        ),
        (
            idom.vdom("div", on_event=FAKE_EVENT_HANDLER),
            {"tagName": "div", "eventHandlers": FAKE_EVENT_HANDLER_DICT},
        ),
        (
            idom.vdom("div", idom.html.h1("hello"), idom.html.h2("world")),
            {
                "tagName": "div",
                "children": [
                    {"tagName": "h1", "children": ["hello"]},
                    {"tagName": "h2", "children": ["world"]},
                ],
            },
        ),
        (
            idom.vdom("div", {"tagName": "div"}),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ),
        (
            idom.vdom("div", (i for i in range(3))),
            {"tagName": "div", "children": [0, 1, 2]},
        ),
        (
            idom.vdom("div", map(lambda x: x**2, [1, 2, 3])),
            {"tagName": "div", "children": [1, 4, 9]},
        ),
        (
            with_import_source(
                idom.vdom("MyComponent"),
                {"source": "./some-script.js", "fallback": "loading..."},
            ),
            {
                "tagName": "MyComponent",
                "importSource": {
                    "source": "./some-script.js",
                    "fallback": "loading...",
                },
            },
        ),
    ],
)
def test_simple_node_construction(actual, expected):
    assert actual == expected


async def test_callable_attributes_are_cast_to_event_handlers():
    params_from_calls = []

    node = idom.vdom("div", on_event=lambda *args: params_from_calls.append(args))

    event_handlers = node.pop("eventHandlers")
    assert node == {"tagName": "div"}

    handler = event_handlers["on_event"]
    assert event_handlers == {"on_event": EventHandler(handler.function)}

    await handler.function([1, 2])
    await handler.function([3, 4, 5])
    assert params_from_calls == [(1, 2), (3, 4, 5)]


def test_make_vdom_constructor():
    elmt = make_vdom_constructor("some-tag")

    assert elmt(elmt(), data=1) == {
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
                "stopPropogation": True,
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
                "stopPropogation": True,
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
            r"data\.children\[{data_x}\] must be object or string",
        ),
        (
            {"tagName": "tag", "children": [{"tagName": None}]},
            r"data\.children\[{data_x}\]\.tagName must be string",
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
            r"data\.eventHandlers\.{data_key} must be object",
        ),
        (
            {
                "tagName": "tag",
                "eventHandlers": {"onEvent": {}},
            },
            r"data\.eventHandlers\.{data_key}\ must contain \['target'\] properties",
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
            r"data\.eventHandlers\.{data_key}\.preventDefault must be boolean",
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
            r"data\.eventHandlers\.{data_key}\.stopPropagation must be boolean",
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


@pytest.mark.skipif(not IDOM_DEBUG_MODE.current, reason="Only logs in debug mode")
def test_debug_log_cannot_verify_keypath_for_genereators(caplog):
    idom.vdom("div", (1 for i in range(10)))
    assert len(caplog.records) == 1
    assert caplog.records[0].message.startswith(
        "Did not verify key-path integrity of children in generator"
    )
    caplog.records.clear()


@pytest.mark.skipif(not IDOM_DEBUG_MODE.current, reason="Only logs in debug mode")
def test_debug_log_dynamic_children_must_have_keys(caplog):
    idom.vdom("div", [idom.vdom("div")])
    assert len(caplog.records) == 1
    assert caplog.records[0].message.startswith("Key not specified for child")

    caplog.records.clear()

    @idom.component
    def MyComponent():
        return idom.vdom("div")

    idom.vdom("div", [MyComponent()])
    assert len(caplog.records) == 1
    assert caplog.records[0].message.startswith("Key not specified for child")
