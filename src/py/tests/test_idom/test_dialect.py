# dialect = html, pytest
import pytest

from pyalect import apply_dialects, DialectError

from idom import html


def test_single_root():
    assert html("<div />") == {"tagName": "div"}


def test_value_children():
    assert html("<div>foo</div>") == {"tagName": "div", "children": ["foo"]}
    assert html("<div><span/></div>") == {
        "tagName": "div",
        "children": [{"tagName": "span"}],
    }


def test_expression_children():
    value = "foo"
    assert html("<div>{value}</div>") == {"tagName": "div", "children": ["foo"]}
    assert html("<div>{html('<span/>')}</div>") == {
        "tagName": "div",
        "children": [{"tagName": "span"}],
    }


def test_preserve_whitespace_between_text_values():
    assert html("<div>  a  {'b'}  c  </div>") == {
        "tagName": "div",
        "children": ["  a  ", "b", "  c  "],
    }


def test_collapse_whitespace_lines_in_text():
    assert html("<div>    \n    a    b    c    \n    </div>") == {
        "tagName": "div",
        "children": ["a    b    c"],
    }
    assert html("<div>a   \n   {'b'}    \n    c    \n    </div>") == {
        "tagName": "div",
        "children": ["a", "b", "c"],
    }


def test_value_tag():
    assert html("<div/>") == {"tagName": "div"}
    assert html("<div />") == {"tagName": "div"}
    assert html("<'div' />") == {"tagName": "div"}
    assert html('<"div" />') == {"tagName": "div"}


def test_expression_tag():
    tag = "div"
    assert html("<{tag} />") == {"tagName": "div"}


def test_boolean_prop():
    assert html("<div foo />") == {"tagName": "div", "attributes": {"foo": True}}
    assert html("<div 'foo' />") == {"tagName": "div", "attributes": {"foo": True}}
    assert html('<div "foo" />') == {"tagName": "div", "attributes": {"foo": True}}


def test_value_prop_name():
    assert html("<div foo=1 />") == {"tagName": "div", "attributes": {"foo": "1"}}
    assert html('<div "foo"=1 />') == {"tagName": "div", "attributes": {"foo": "1"}}
    assert html("<div 'foo'=1 />") == {"tagName": "div", "attributes": {"foo": "1"}}
    assert html("<div foo='1' />") == {"tagName": "div", "attributes": {"foo": "1"}}
    assert html('<div foo="1" />') == {"tagName": "div", "attributes": {"foo": "1"}}


def test_expression_prop_value():
    a = 1
    assert html("<div foo={a} />") == {"tagName": "div", "attributes": {"foo": 1}}
    assert html('<div "foo"={a} />') == {"tagName": "div", "attributes": {"foo": 1}}
    assert html("<div 'foo'={a} />") == {"tagName": "div", "attributes": {"foo": 1}}


def test_concatenated_prop_value():
    a = 1
    assert html("<div foo={a}{2} />") == {"tagName": "div", "attributes": {"foo": "12"}}
    assert html("<div foo=0/{a}/{2} />") == {
        "tagName": "div",
        "attributes": {"foo": "0/1/2"},
    }


def test_slash_in_prop_value():
    assert html("<div foo=/bar/quux />") == {
        "tagName": "div",
        "attributes": {"foo": "/bar/quux"},
    }


def test_spread():
    foo = {"foo": 1}
    assert html("<div ...{foo} ...{({'bar': 2})} />") == {
        "tagName": "div",
        "attributes": {"foo": 1, "bar": 2},
    }


def test_comments():
    assert (
        html(
            """
            <div>
                before
                <!--
                    multiple lines, {"variables"} and "quotes
                    get ignored
                -->
                after
            </div>
            """
        )
        == {"tagName": "div", "children": ["before", "after"]}
    )
    assert html("<div><!-->slight deviation from HTML comments<--></div>") == {
        "tagName": "div"
    }


def test_tag_errors():
    with pytest.raises(DialectError, match="no token found"):
        apply_dialects("""html("< >")""", "html")
    with pytest.raises(DialectError, match="no token found"):
        apply_dialects("""html("<>")""", "html")
    with pytest.raises(DialectError, match="no token found"):
        apply_dialects("""html("<'")""", "html")
    with pytest.raises(DialectError, match="unexpected end of data"):
        apply_dialects("""html("<")""", "html")


def test_attribute_name_errors():
    with pytest.raises(DialectError, match="expression not allowed"):
        apply_dialects("""html("<div {1}>")""", "html")
    with pytest.raises(DialectError, match="unexpected end of data"):
        apply_dialects("""html("<div ")""", "html")
    with pytest.raises(DialectError, match="no token found"):
        apply_dialects("""html("<div '")""", "html")


def test_attribute_value_errors():
    with pytest.raises(DialectError, match="invalid character"):
        apply_dialects("""html("<div 'a'x")""", "html")
    with pytest.raises(DialectError, match="expression not allowed"):
        apply_dialects("""html("<div a{1}")""", "html")
    with pytest.raises(DialectError, match="unexpected end of data"):
        apply_dialects("""html("<div a")""", "html")
    with pytest.raises(DialectError, match="unexpected end of data"):
        apply_dialects("""html("<div a=")""", "html")


def test_structural_errors():
    with pytest.raises(DialectError, match="all opened tags not closed"):
        apply_dialects("""html("<div>")""", "html")
