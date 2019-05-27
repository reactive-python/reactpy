import pytest

import idom
from idom.tools import html_to_vdom


def test_var_equivalence():
    r1 = idom.Var([1, 2, 3])
    r2 = idom.Var([1, 2, 3])
    assert r1 == r2


def test_var_set():
    v = idom.Var(None)
    old_1 = v.set("new_1")
    assert old_1 is None
    old_2 = v.set("new_2")
    assert old_2 == "new_1"


def test_var_get():
    v = idom.Var(None)
    assert v.get() is None
    v.set(1)
    assert v.get() == 1


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
    assert html_to_vdom(case["source"]) == {
        "tagName": "div",
        "children": [case["model"]],
    }


def test_html_to_vdom_transform():
    source = "<p>hello <a>world</a> and <a>universe</a></p>"

    def make_links_blue(node):
        if node["tagName"] == "a":
            node["attributes"]["style"] = {"color": "blue"}
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
        ],
    }

    assert html_to_vdom(source, make_links_blue) == {
        "tagName": "div",
        "children": [expected],
    }
