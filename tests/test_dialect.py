import ast
from typing import Tuple, Dict, Any, Any

import pytest
from pyalect import apply_dialects, DialectError

from idom import html


def eval_html(src, variables=None):
    tree = apply_dialects(src, "html")
    if len(tree.body) > 1 or not isinstance(tree.body[0], ast.Expr):
        raise ValueError(f"Expected a single expression, not {src!r}")
    code = compile(ast.Expression(tree.body[0].value), "<string>", "eval")
    return eval(code, {"html": html}, variables)


def make_html_dialect_test(*expectations: Tuple[str, Dict[str, Any], Any]):
    def make_ids(exp):
        source, variables = exp[:2]
        source_repr = repr(source)
        if len(source_repr) > 30:
            source_repr = source_repr[:30] + "'..."
        variables_repr = repr(variables)
        if len(variables_repr) > 30:
            variables_repr = variables_repr[:30] + "...}"
        return source_repr + "-" + variables_repr

    @pytest.mark.parametrize("expect", expectations, ids=make_ids)
    def test_html_dialect(expect):
        source, variables, result = expect
        assert eval_html(source, variables) == result

    return test_html_dialect


test_simple_htm_template = make_html_dialect_test(
    ('html(f"<div />")', {}, {"tagName": "div"})
)

test_value_children = make_html_dialect_test(
    ('html(f"<div>foo</div>")', {}, {"tagName": "div", "children": ["foo"]}),
    (
        'html(f"<div><span/></div>")',
        {},
        {"tagName": "div", "children": [{"tagName": "span"}]},
    ),
)

test_expression_children = make_html_dialect_test(
    (
        'html(f"<div>{value}</div>")',
        {"value": "foo"},
        {"tagName": "div", "children": ["foo"]},
    ),
    (
        """html(f"<div>{html(f'<span/>')}</div>")""",
        {},
        {"tagName": "div", "children": [{"tagName": "span"}]},
    ),
)

test_preserve_whitespace_between_text_values = make_html_dialect_test(
    (
        """html(f"<div>  a  {'b'}  c  </div>")""",
        {},
        {"tagName": "div", "children": ["  a  ", "b", "  c  "]},
    )
)

test_collapse_whitespace_lines_in_text = make_html_dialect_test(
    (
        r'html(f"<div>    \n    a    b    c    \n    </div>")',
        {},
        {"tagName": "div", "children": ["a    b    c"]},
    ),
    (
        r"""html(f"<div>a   \n   {'b'}   \n    c    \n    </div>")""",
        {},
        {"tagName": "div", "children": ["a", "b", "c"]},
    ),
)

test_value_tag = make_html_dialect_test(
    ('html(f"<div/>")', {}, {"tagName": "div"}),
    ('html(f"<div />")', {}, {"tagName": "div"}),
    ("""html(f"<'div' />")""", {}, {"tagName": "div"}),
    ("""html(f'<"div" />')""", {}, {"tagName": "div"}),
)

test_expression_tag = make_html_dialect_test(
    ('html(f"<{tag} />")', {"tag": "div"}, {"tagName": "div"})
)

test_boolean_prop = make_html_dialect_test(
    ('html(f"<div foo />")', {}, {"tagName": "div", "attributes": {"foo": True}}),
    ("""html(f"<div 'foo' />")""", {}, {"tagName": "div", "attributes": {"foo": True}}),
    ("""html(f'<div "foo" />')""", {}, {"tagName": "div", "attributes": {"foo": True}}),
)

test_value_prop_name = make_html_dialect_test(
    ('html(f"<div foo=1 />")', {}, {"tagName": "div", "attributes": {"foo": "1"}}),
    (
        """html(f'<div "foo"=1 />')""",
        {},
        {"tagName": "div", "attributes": {"foo": "1"}},
    ),
    (
        """html(f"<div 'foo'=1 />")""",
        {},
        {"tagName": "div", "attributes": {"foo": "1"}},
    ),
    (
        """html(f"<div foo='1' />")""",
        {},
        {"tagName": "div", "attributes": {"foo": "1"}},
    ),
    (
        """html(f'<div foo="1" />')""",
        {},
        {"tagName": "div", "attributes": {"foo": "1"}},
    ),
)

test_expression_prop_value = make_html_dialect_test(
    (
        """html(f"<div foo={a} />")""",
        {"a": 1.23},
        {"tagName": "div", "attributes": {"foo": 1.23}},
    ),
    (
        """html(f'<div "foo"={a} />')""",
        {"a": 1.23},
        {"tagName": "div", "attributes": {"foo": 1.23}},
    ),
    (
        """html(f"<div 'foo'={a} />")""",
        {"a": 1.23},
        {"tagName": "div", "attributes": {"foo": 1.23}},
    ),
    (
        """html(f"<div foo={a:.2} />")""",
        {"a": 1.23},
        {"tagName": "div", "attributes": {"foo": "1.2"}},
    ),
)

test_concatenated_prop_value = make_html_dialect_test(
    (
        """html(f"<div foo={a}{'2'} />")""",
        {"a": "1"},
        {"tagName": "div", "attributes": {"foo": "12"}},
    ),
    (
        """html(f"<div foo=0/{a}/{'2'} />")""",
        {"a": "1"},
        {"tagName": "div", "attributes": {"foo": "0/1/2"}},
    ),
)


test_slash_in_prop_value = make_html_dialect_test(
    (
        """html(f"<div foo=/bar/quux />")""",
        {},
        {"tagName": "div", "attributes": {"foo": "/bar/quux"}},
    )
)


test_spread = make_html_dialect_test(
    (
        """html(f"<div ...{foo} ...{({'bar': 2})} />")""",
        {"foo": {"foo": 1}},
        {"tagName": "div", "attributes": {"foo": 1, "bar": 2}},
    )
)


test_comments = make_html_dialect_test(
    (
        '''html(
            f"""
            <div>
                before
                <!--
                    multiple lines, {"variables"} and "quotes
                    get ignored
                -->
                after
            </div>
            """
        )''',
        {},
        {"tagName": "div", "children": ["before", "after"]},
    ),
    (
        """html(f"<div><!-->slight deviation from HTML comments<--></div>")""",
        {},
        {"tagName": "div"},
    ),
)


test_component = make_html_dialect_test(
    (
        'html(f"<{MyComponentWithChildren}>hello<//>")',
        {"MyComponentWithChildren": lambda children: html.div(children + ["world"])},
        {"tagName": "div", "children": ["hello", "world"]},
    ),
    (
        'html(f"<{MyComponentWithAttributes} x=2 y=3 />")',
        {
            "MyComponentWithAttributes": lambda x, y: html.div(
                {"x": int(x) * 2, "y": int(y) * 2}
            )
        },
        {"tagName": "div", "attributes": {"x": 4, "y": 6}},
    ),
    (
        'html(f"<{MyComponentWithAttributesAndChildren} x=2 y=3>hello<//>")',
        {
            "MyComponentWithAttributesAndChildren": lambda x, y, children: html.div(
                {"x": int(x) * 2, "y": int(y) * 2}, children + ["world"]
            )
        },
        {
            "tagName": "div",
            "attributes": {"x": 4, "y": 6},
            "children": ["hello", "world"],
        },
    ),
)


def test_tag_errors():
    with pytest.raises(DialectError, match="no token found"):
        apply_dialects('html(f"< >")', "html")
    with pytest.raises(DialectError, match="no token found"):
        apply_dialects('html(f"<>")', "html")
    with pytest.raises(DialectError, match="no token found"):
        apply_dialects("""html(f"<'")""", "html")
    with pytest.raises(DialectError, match="unexpected end of data"):
        apply_dialects('html(f"<")', "html")


def test_attribute_name_errors():
    with pytest.raises(DialectError, match="expression not allowed"):
        apply_dialects('html(f"<div {1}>")', "html")
    with pytest.raises(DialectError, match="unexpected end of data"):
        apply_dialects('html(f"<div ")', "html")
    with pytest.raises(DialectError, match="no token found"):
        apply_dialects("""html(f"<div '")""", "html")


def test_attribute_value_errors():
    with pytest.raises(DialectError, match="invalid character"):
        apply_dialects("""html(f"<div 'a'x")""", "html")
    with pytest.raises(DialectError, match="unexpected end of data"):
        apply_dialects('html(f"<div a{1}")', "html")
    with pytest.raises(DialectError, match="unexpected end of data"):
        apply_dialects('html(f"<div a")', "html")
    with pytest.raises(DialectError, match="unexpected end of data"):
        apply_dialects('html(f"<div a=")', "html")


def test_structural_errors():
    with pytest.raises(DialectError, match="all opened tags not closed"):
        apply_dialects('html(f"<div>")', "html")
