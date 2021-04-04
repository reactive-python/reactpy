import pytest
from fastjsonschema import JsonSchemaException

import idom
from idom.core.vdom import make_vdom_constructor, validate_vdom


fake_events = idom.Events()


@fake_events.on("Click")
async def handler(event):
    pass


@pytest.mark.parametrize(
    "actual, expected",
    [
        (
            idom.vdom("div", [idom.vdom("div")]),
            {"tagName": "div", "children": [{"tagName": "div"}]},
        ),
        (
            idom.vdom("div", {"style": {"backgroundColor": "red"}}),
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
            # multiple dictionaries of attributes are merged
            idom.vdom("div", {"width": "30px"}, {"height": "20px"}),
            {"tagName": "div", "attributes": {"width": "30px", "height": "20px"}},
        ),
        (
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
        ),
        (
            idom.vdom("div", event_handlers=fake_events),
            {"tagName": "div", "eventHandlers": fake_events},
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
            idom.vdom("div", map(lambda x: x ** 2, [1, 2, 3])),
            {"tagName": "div", "children": [1, 4, 9]},
        ),
        (
            idom.vdom(
                "MyComponent",
                import_source={"source": "./some-script.js", "fallback": "loading..."},
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
    validate_vdom(value)


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
            r"data must be array",
        ),
        (
            {"tagName": "tag", "children": [None]},
            r"data must be object or string",
        ),
        (
            {"tagName": "tag", "children": [{"tagName": None}]},
            r"data\.tagName must be string",
        ),
        (
            {"tagName": "tag", "attributes": None},
            r"data.attributes must be object",
        ),
        (
            {"tagName": "tag", "eventHandlers": None},
            r"data must be object",
        ),
        (
            {"tagName": "tag", "eventHandlers": {"onEvent": None}},
            r"data must be object",
        ),
        (
            {
                "tagName": "tag",
                "eventHandlers": {"onEvent": {}},
            },
            r"data must contain \['target'\] properties",
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
            r"data\.preventDefault must be boolean",
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
            r"data\.stopPropagation must be boolean",
        ),
        (
            {"tagName": "tag", "importSource": None},
            r"data must be object",
        ),
        (
            {"tagName": "tag", "importSource": {}},
            r"data must contain \['source'\] properties",
        ),
        (
            {
                "tagName": "tag",
                "importSource": {"source": "something", "fallback": 0},
            },
            r"data\.fallback must be object or string or null",
        ),
        (
            {
                "tagName": "tag",
                "importSource": {"source": "something", "fallback": {"tagName": None}},
            },
            r"data.tagName must be string",
        ),
    ],
)
def test_invalid_vdom(value, error_message_pattern):
    with pytest.raises(JsonSchemaException, match=error_message_pattern):
        validate_vdom(value)
