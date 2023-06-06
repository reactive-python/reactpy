from html import escape as html_escape

import pytest

import reactpy
from reactpy import html
from reactpy.utils import (
    HTMLParseError,
    del_html_head_body_transform,
    html_to_vdom,
    vdom_to_html,
)


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
        {"source": "<div/>", "model": {"tagName": "div"}},
        {
            "source": "<div style='background-color:blue'/>",
            "model": {
                "tagName": "div",
                "attributes": {"style": {"background_color": "blue"}},
            },
        },
        {
            "source": "<div>Hello!</div>",
            "model": {"tagName": "div", "children": ["Hello!"]},
        },
        {
            "source": "<div>Hello!<p>World!</p></div>",
            "model": {
                "tagName": "div",
                "children": ["Hello!", {"tagName": "p", "children": ["World!"]}],
            },
        },
    ],
)
def test_html_to_vdom(case):
    assert html_to_vdom(case["source"]) == case["model"]


def test_html_to_vdom_transform():
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

    assert html_to_vdom(source, make_links_blue) == expected


def test_non_html_tag_behavior():
    source = "<my-tag data-x=something><my-other-tag key=a-key /></my-tag>"

    expected = {
        "tagName": "my-tag",
        "attributes": {"data-x": "something"},
        "children": [
            {"tagName": "my-other-tag", "key": "a-key"},
        ],
    }

    assert html_to_vdom(source, strict=False) == expected

    with pytest.raises(HTMLParseError):
        html_to_vdom(source, strict=True)


def test_html_to_vdom_with_null_tag():
    source = "<p>hello<br>world</p>"

    expected = {
        "tagName": "p",
        "children": [
            "hello",
            {"tagName": "br"},
            "world",
        ],
    }

    assert html_to_vdom(source) == expected


def test_html_to_vdom_with_style_attr():
    source = '<p style="color: red; background-color : green; ">Hello World.</p>'

    expected = {
        "attributes": {"style": {"background_color": "green", "color": "red"}},
        "children": ["Hello World."],
        "tagName": "p",
    }

    assert html_to_vdom(source) == expected


def test_html_to_vdom_with_no_parent_node():
    source = "<p>Hello</p><div>World</div>"

    expected = {
        "tagName": "div",
        "children": [
            {"tagName": "p", "children": ["Hello"]},
            {"tagName": "div", "children": ["World"]},
        ],
    }

    assert html_to_vdom(source) == expected


def test_del_html_body_transform():
    source = """
    <!DOCTYPE html>
    <html lang="en">

    <head>
    <title>My Title</title>
    </head>

    <body><h1>Hello World</h1></body>

    </html>
    """

    expected = {
        "tagName": "",
        "children": [
            {
                "tagName": "",
                "children": [{"tagName": "title", "children": ["My Title"]}],
            },
            {
                "tagName": "",
                "children": [{"tagName": "h1", "children": ["Hello World"]}],
            },
        ],
    }

    assert html_to_vdom(source, del_html_head_body_transform) == expected


SOME_OBJECT = object()


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
            html.button({"on_click": lambda event: None}),
            "<button></button>",
        ),
        (
            html._("hello ", html._("world")),
            "hello world",
        ),
        (
            html._(html.div("hello"), html._("world")),
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
            html._(
                html.div("hello"),
                html.a({"href": "https://example.com"}, "example"),
            ),
            '<div>hello</div><a href="https://example.com">example</a>',
        ),
        (
            html.div(
                html._(
                    html.div("hello"),
                    html.a({"href": "https://example.com"}, "example"),
                ),
                html.button(),
            ),
            '<div><div>hello</div><a href="https://example.com">example</a><button></button></div>',
        ),
        (
            html.div(
                {"data_something": 1, "data_something_else": 2, "dataisnotdashed": 3}
            ),
            '<div data-something="1" data-something-else="2" dataisnotdashed="3"></div>',
        ),
        (
            html.div(
                {"dataSomething": 1, "dataSomethingElse": 2, "dataisnotdashed": 3}
            ),
            '<div data-something="1" data-something-else="2" dataisnotdashed="3"></div>',
        ),
    ],
)
def test_vdom_to_html(vdom_in, html_out):
    assert vdom_to_html(vdom_in) == html_out


def test_vdom_to_html_error():
    with pytest.raises(TypeError, match="Expected a VDOM dict"):
        vdom_to_html({"notVdom": True})
