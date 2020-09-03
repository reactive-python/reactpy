import pytest

import idom
from idom.utils import html_to_vdom


def test_basic_ref_behavior():
    r = idom.Ref(1)
    assert r.current == 1

    r.current = 2
    assert r.current == 2

    assert r.set_current(3) == 2
    assert r.current == 3


def test_ref_equivalence():
    assert idom.Ref([1, 2, 3]) == idom.Ref([1, 2, 3])
    assert idom.Ref([1, 2, 3]) != idom.Ref([1, 2])
    assert idom.Ref([1, 2, 3]) != [1, 2, 3]


def test_ref_repr():
    assert repr(idom.Ref([1, 2, 3])) == "Ref([1, 2, 3])"


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
