from html import escape as html_escape

import pytest

import reactpy
from reactpy import component, html, utils


def test_basic_ref_behavior():
    r = reactpy.Ref(1)
    assert r.current == 1

    r.current = 2
    assert r.current == 2

    assert r.set_current(3) == 2
    assert r.current == 3

    r = reactpy.Ref()
    with pytest.raises(AttributeError):
        r.current  # noqa: B018

    r.current = 4
    assert r.current == 4


def test_ref_equivalence():
    assert reactpy.Ref([1, 2, 3]) == reactpy.Ref([1, 2, 3])
    assert reactpy.Ref([1, 2, 3]) != reactpy.Ref([1, 2])
    assert reactpy.Ref([1, 2, 3]) != [1, 2, 3]
    assert reactpy.Ref() != reactpy.Ref()
    assert reactpy.Ref() != reactpy.Ref(1)


def test_ref_repr():
    assert repr(reactpy.Ref([1, 2, 3])) == "Ref([1, 2, 3])"
    assert repr(reactpy.Ref()) == "Ref(<undefined>)"


@pytest.mark.parametrize(
    "case",
    [
        # 0: Single terminating tag
        {"source": "<div/>", "model": {"tagName": "div"}},
        # 1: Single terminating tag with attributes
        {
            "source": "<div style='background-color:blue'/>",
            "model": {
                "tagName": "div",
                "attributes": {"style": {"backgroundColor": "blue"}},
            },
        },
        # 2: Single tag with closure and a text-based child
        {
            "source": "<div>Hello!</div>",
            "model": {"tagName": "div", "children": ["Hello!"]},
        },
        # 3: Single tag with closure and a tag-based child
        {
            "source": "<div>Hello!<p>World!</p></div>",
            "model": {
                "tagName": "div",
                "children": ["Hello!", {"tagName": "p", "children": ["World!"]}],
            },
        },
        # 4: A snippet with no root HTML node
        {
            "source": "<p>Hello</p><div>World</div>",
            "model": {
                "tagName": "div",
                "children": [
                    {"tagName": "p", "children": ["Hello"]},
                    {"tagName": "div", "children": ["World"]},
                ],
            },
        },
        # 5: Self-closing tags
        {
            "source": "<p>hello<br>world</p>",
            "model": {
                "tagName": "p",
                "children": [
                    "hello",
                    {"tagName": "br"},
                    "world",
                ],
            },
        },
    ],
)
def test_string_to_reactpy(case):
    assert utils.string_to_reactpy(case["source"]) == case["model"]


@pytest.mark.parametrize(
    "case",
    [
        # 0: Style attribute transformation
        {
            "source": '<p style="color: red; background-color : green; ">Hello World.</p>',
            "model": {
                "tagName": "p",
                "attributes": {"style": {"backgroundColor": "green", "color": "red"}},
                "children": ["Hello World."],
            },
        },
        # 1: Convert HTML style properties to ReactJS style
        {
            "source": '<p class="my-class">Hello World.</p>',
            "model": {
                "tagName": "p",
                "attributes": {"className": "my-class"},
                "children": ["Hello World."],
            },
        },
        # 2: Convert <textarea> children into the ReactJS `defaultValue` prop
        {
            "source": "<textarea>Hello World.</textarea>",
            "model": {
                "tagName": "textarea",
                "attributes": {"defaultValue": "Hello World."},
            },
        },
        # 3: Convert <select> trees into ReactJS equivalent
        {
            "source": "<select><option selected>Option 1</option></select>",
            "model": {
                "tagName": "select",
                "attributes": {"defaultValue": "Option 1"},
                "children": [
                    {
                        "children": ["Option 1"],
                        "tagName": "option",
                        "attributes": {"value": "Option 1"},
                    }
                ],
            },
        },
        # 4: Convert <select> trees into ReactJS equivalent (multiple choice, multiple selected)
        {
            "source": "<select multiple><option selected>Option 1</option><option selected>Option 2</option></select>",
            "model": {
                "tagName": "select",
                "attributes": {
                    "defaultValue": ["Option 1", "Option 2"],
                    "multiple": True,
                },
                "children": [
                    {
                        "children": ["Option 1"],
                        "tagName": "option",
                        "attributes": {"value": "Option 1"},
                    },
                    {
                        "children": ["Option 2"],
                        "tagName": "option",
                        "attributes": {"value": "Option 2"},
                    },
                ],
            },
        },
        # 5: Convert <input> value attribute into `defaultValue`
        {
            "source": '<input type="text" value="Hello World.">',
            "model": {
                "tagName": "input",
                "attributes": {"defaultValue": "Hello World.", "type": "text"},
            },
        },
        # 6: Infer ReactJS `key` from the `id` attribute
        {
            "source": '<div id="my-key"></div>',
            "model": {
                "tagName": "div",
                "key": "my-key",
                "attributes": {"id": "my-key"},
            },
        },
        # 7: Infer ReactJS `key` from the `name` attribute
        {
            "source": '<input type="text" name="my-input">',
            "model": {
                "tagName": "input",
                "key": "my-input",
                "attributes": {"type": "text", "name": "my-input"},
            },
        },
        # 8: Infer ReactJS `key` from the `key` attribute
        {
            "source": '<div key="my-key"></div>',
            "model": {
                "tagName": "div",
                "attributes": {"key": "my-key"},
                "key": "my-key",
            },
        },
    ],
)
def test_string_to_reactpy_default_transforms(case):
    assert utils.string_to_reactpy(case["source"]) == case["model"]


def test_string_to_reactpy_intercept_links():
    source = '<a href="https://example.com">Hello World</a>'
    expected = {
        "tagName": "a",
        "children": ["Hello World"],
        "attributes": {"href": "https://example.com"},
    }
    result = utils.string_to_reactpy(source, intercept_links=True)

    # Check if the result equals expected when removing `eventHandlers` from the result dict
    event_handlers = result.pop("eventHandlers", {})
    assert result == expected

    # Make sure the event handlers dict contains an `onClick` key
    assert "onClick" in event_handlers


def test_string_to_reactpy_custom_transform():
    source = "<p>hello <a>world</a> and <a>universe</a>lmao</p>"

    def make_links_blue(node):
        if node["tagName"] == "a":
            node["attributes"] = {"style": {"color": "blue"}}
        return node

    expected = {
        "tagName": "p",
        "children": [
            "hello ",
            {
                "tagName": "a",
                "children": ["world"],
                "attributes": {"style": {"color": "blue"}},
            },
            " and ",
            {
                "tagName": "a",
                "children": ["universe"],
                "attributes": {"style": {"color": "blue"}},
            },
            "lmao",
        ],
    }

    assert (
        utils.string_to_reactpy(source, make_links_blue, intercept_links=False)
        == expected
    )


def test_non_html_tag_behavior():
    source = "<my-tag data-x=something><my-other-tag key=a-key /></my-tag>"

    expected = {
        "tagName": "my-tag",
        "attributes": {"data-x": "something"},
        "children": [
            {"tagName": "my-other-tag", "attributes": {"key": "a-key"}, "key": "a-key"},
        ],
    }

    assert utils.string_to_reactpy(source, strict=False) == expected

    with pytest.raises(utils.HTMLParseError):
        utils.string_to_reactpy(source, strict=True)


SOME_OBJECT = object()


@component
def example_parent():
    return example_middle()


@component
def example_middle():
    return html.div({"id": "sample", "style": {"padding": "15px"}}, example_child())


@component
def example_child():
    return html.h1("Example")


@component
def example_str_return():
    return "Example"


@component
def example_none_return():
    return None


@pytest.mark.parametrize(
    "vdom_in, html_out",
    [
        (
            html.div("hello"),
            "<div>hello</div>",
        ),
        (
            html.div(SOME_OBJECT),
            f"<div>{html_escape(str(SOME_OBJECT))}</div>",
        ),
        (
            html.div(
                "hello", html.a({"href": "https://example.com"}, "example"), "world"
            ),
            '<div>hello<a href="https://example.com">example</a>world</div>',
        ),
        (
            html.button({"onClick": lambda event: None}),
            "<button></button>",
        ),
        (
            html.fragment("hello ", html.fragment("world")),
            "hello world",
        ),
        (
            html.fragment(html.div("hello"), html.fragment("world")),
            "<div>hello</div>world",
        ),
        (
            html.div({"style": {"backgroundColor": "blue", "marginLeft": "10px"}}),
            '<div style="background-color:blue;margin-left:10px"></div>',
        ),
        (
            html.div({"style": "background-color:blue;margin-left:10px"}),
            '<div style="background-color:blue;margin-left:10px"></div>',
        ),
        (
            html.fragment(
                html.div("hello"),
                html.a({"href": "https://example.com"}, "example"),
            ),
            '<div>hello</div><a href="https://example.com">example</a>',
        ),
        (
            html.div(
                html.fragment(
                    html.div("hello"),
                    html.a({"href": "https://example.com"}, "example"),
                ),
                html.button(),
            ),
            '<div><div>hello</div><a href="https://example.com">example</a><button></button></div>',
        ),
        (
            html.div({"data-Something": 1, "dataCamelCase": 2, "datalowercase": 3}),
            '<div data-Something="1" datacamelcase="2" datalowercase="3"></div>',
        ),
        (
            html.div(example_parent()),
            '<div><div id="sample" style="padding:15px"><h1>Example</h1></div></div>',
        ),
        (
            example_parent(),
            '<div id="sample" style="padding:15px"><h1>Example</h1></div>',
        ),
        (
            html.form({"acceptCharset": "utf-8"}),
            '<form accept-charset="utf-8"></form>',
        ),
        (
            example_str_return(),
            "<div>Example</div>",
        ),
        (
            example_none_return(),
            "",
        ),
    ],
)
def test_reactpy_to_string(vdom_in, html_out):
    assert utils.reactpy_to_string(vdom_in) == html_out


def test_reactpy_to_string_error():
    with pytest.raises(TypeError, match="Expected a VDOM dict"):
        utils.reactpy_to_string({"notVdom": True})


def test_invalid_dotted_path():
    with pytest.raises(ValueError, match='"abc" is not a valid dotted path.'):
        utils.import_dotted_path("abc")


def test_invalid_component():
    with pytest.raises(
        AttributeError, match='ReactPy failed to import "foobar" from "reactpy"'
    ):
        utils.import_dotted_path("reactpy.foobar")


def test_invalid_module():
    with pytest.raises(ImportError, match='ReactPy failed to import "foo"'):
        utils.import_dotted_path("foo.bar")
