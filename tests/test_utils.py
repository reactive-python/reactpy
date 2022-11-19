import pytest

import idom
from idom import html
from idom.utils import HTMLParseError, html_to_vdom, vdom_to_html


def test_basic_ref_behavior():
    r = idom.Ref(1)
    assert r.current == 1

    r.current = 2
    assert r.current == 2

    assert r.set_current(3) == 2
    assert r.current == 3

    r = idom.Ref()
    with pytest.raises(AttributeError):
        r.current

    r.current = 4
    assert r.current == 4


def test_ref_equivalence():
    assert idom.Ref([1, 2, 3]) == idom.Ref([1, 2, 3])
    assert idom.Ref([1, 2, 3]) != idom.Ref([1, 2])
    assert idom.Ref([1, 2, 3]) != [1, 2, 3]
    assert idom.Ref() != idom.Ref()
    assert idom.Ref() != idom.Ref(1)


def test_ref_repr():
    assert repr(idom.Ref([1, 2, 3])) == "Ref([1, 2, 3])"
    assert repr(idom.Ref()) == "Ref(<undefined>)"


@pytest.mark.parametrize(
    "case",
    [
        {"source": "<div/>", "model": {"tagName": "div"}},
        {
            "source": "<div style='background-color:blue'/>",
            "model": {
                "tagName": "div",
                "attributes": {"style": {"backgroundColor": "blue"}},
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
        "attributes": {"style": {"backgroundColor": "green", "color": "red"}},
        "children": ["Hello World."],
        "tagName": "p",
    }

    assert html_to_vdom(source) == expected


def test_html_to_vdom_with_no_parent_node():
    source = "<p>Hello</p><div>World</div>"

    expected = {
        "tagName": "",
        "children": [
            {"tagName": "p", "children": ["Hello"]},
            {"tagName": "div", "children": ["World"]},
        ],
    }

    assert html_to_vdom(source) == expected


@pytest.mark.parametrize(
    "vdom_in, html_out",
    [
        (
            html.div("hello"),
            "<div>hello</div>",
        ),
        (
            html.div(object()),  # ignore non-str/vdom children
            "<div />",
        ),
        (
            html.div({"someAttribute": object()}),  # ignore non-str/vdom attrs
            "<div />",
        ),
        (
            html.div("hello", html.a({"href": "https://example.com"}, "example")),
            '<div>hello<a href="https://example.com">example</a></div>',
        ),
        (
            html.button({"onClick": lambda event: None}),
            "<button />",
        ),
        (
            html.div({"style": {"backgroundColor": "blue", "marginLeft": "10px"}}),
            '<div style="background-color:blue;margin-left:10px" />',
        ),
        (
            html.div({"style": "background-color:blue;margin-left:10px"}),
            '<div style="background-color:blue;margin-left:10px" />',
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
            '<div><div>hello</div><a href="https://example.com">example</a><button /></div>',
        ),
    ],
)
def test_vdom_to_html(vdom_in, html_out):
    assert vdom_to_html(vdom_in) == html_out


def test_vdom_to_html_with_indent():
    assert (
        vdom_to_html(
            html.div("hello", html.a({"href": "https://example.com"}, "example")),
            indent=2,
        )
        == '<div>\n  hello\n  <a href="https://example.com">\n    example\n  </a>\n</div>'
    )
