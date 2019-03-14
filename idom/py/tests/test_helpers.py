import pytest

import idom


_expected_nodes = [
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
]


@pytest.mark.parametrize("actual, expected", _expected_nodes)
def test_node(actual, expected):
    assert actual == expected


def test_ref_equivalence():
    r1 = idom.Ref([1, 2, 3])
    r2 = idom.Ref([1, 2, 3])
    assert r1 == r2
