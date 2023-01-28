import sys
from pathlib import Path
from textwrap import dedent

import pytest
from click.testing import CliRunner

from idom._console.update_html_usages import generate_rewrite, update_html_usages


if sys.version_info < (3, 9):
    pytestmark = pytest.mark.skip(reason="ast.unparse is Python>=3.9")


def test_update_html_usages(tmp_path):
    runner = CliRunner()

    tempfile: Path = tmp_path / "temp.py"
    tempfile.write_text("html.div({'className': test})")
    result = runner.invoke(
        update_html_usages,
        args=[str(tmp_path)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert tempfile.read_text() == "html.div(class_name=test)"


def test_update_html_usages_no_files():
    runner = CliRunner()

    result = runner.invoke(
        update_html_usages, args=["directory-does-no-exist"], catch_exceptions=False
    )

    assert result.exit_code != 0


@pytest.mark.parametrize(
    "source, expected",
    [
        (
            'html.div({"className": "test"})',
            "html.div(class_name='test')",
        ),
        (
            'vdom("div", {"className": "test"})',
            "vdom('div', class_name='test')",
        ),
        (
            'html.div({variable: "test", **other, "key": value})',
            "html.div(**{variable: 'test', **other, 'key': value})",
        ),
        (
            'html.div(dict(other, className="test", **another))',
            "html.div(**other, class_name='test', **another)",
        ),
        (
            'html.div({"className": "outer"}, html.div({"className": "inner"}))',
            "html.div(html.div(class_name='inner'), class_name='outer')",
        ),
        (
            'html.div({"className": "outer"}, html.div({"className": "inner"}))',
            "html.div(html.div(class_name='inner'), class_name='outer')",
        ),
        (
            '["before", html.div({"className": "test"}), "after"]',
            "['before', html.div(class_name='test'), 'after']",
        ),
        (
            """
            html.div(
                {"className": "outer"},
                html.div({"className": "inner"}),
                html.div({"className": "inner"}),
            )
            """,
            "html.div(html.div(class_name='inner'), html.div(class_name='inner'), class_name='outer')",
        ),
        (
            'html.div(dict(className="test"))',
            "html.div(class_name='test')",
        ),
        # when to not attempt conversion
        (
            'html.div(ignore, {"className": "test"})',
            None,
        ),
        (
            "html.div()",
            None,
        ),
        (
            'html.vdom("div")',
            None,
        ),
        (
            'html.div({"tagName": "test"})',
            None,
        ),
        (
            'html.div(dict(tagName="test"))',
            None,
        ),
        (
            'html.not_an_html_tag({"className": "test"})',
            None,
        ),
        (
            'html.div(class_name="test")',
            None,
        ),
        (
            # we don't try to interpret the logic here
            '(div or button)({"className": "test"})',
            None,
        ),
        # avoid unnecessary changes
        (
            """
            def my_function():
                x = 1  # some comment
                return html.div({"className": "test"})
            """,
            """
            def my_function():
                x = 1  # some comment
                return html.div(class_name='test')
            """,
        ),
        (
            """
            if condition:
                # some comment
                dom = html.div({"className": "test"})
            """,
            """
            if condition:
                # some comment
                dom = html.div(class_name='test')
            """,
        ),
        (
            """
            [
                html.div({"className": "test"}),
                html.div({"className": "test"}),
            ]
            """,
            """
            [
                html.div(class_name='test'),
                html.div(class_name='test'),
            ]
            """,
        ),
        (
            """
            @deco(
                html.div({"className": "test"}),
                html.div({"className": "test"}),
            )
            def func():
                # comment
                x = [
                    1
                ]
            """,
            """
            @deco(
                html.div(class_name='test'),
                html.div(class_name='test'),
            )
            def func():
                # comment
                x = [
                    1
                ]
            """,
        ),
        (
            """
            @deco(html.div({"className": "test"}), html.div({"className": "test"}))
            def func():
                # comment
                x = [
                    1
                ]
            """,
            """
            @deco(html.div(class_name='test'), html.div(class_name='test'))
            def func():
                # comment
                x = [
                    1
                ]
            """,
        ),
        (
            """
            (
                result
                if condition
                else html.div({"className": "test"})
            )
            """,
            """
            (
                result
                if condition
                else html.div(class_name='test')
            )
            """,
        ),
        # best effort to preserve comments
        (
            """
            x = 1
            html.div(
                # comment 1
                {"className": "outer"},
                # comment 2
                html.div({"className": "inner"}),
            )
            """,
            """
            x = 1
            # comment 1
            # comment 2
            html.div(html.div(class_name='inner'), class_name='outer')
            """,
        ),
    ],
    ids=lambda item: " ".join(map(str.strip, item.split()))
    if isinstance(item, str)
    else item,
)
def test_generate_rewrite(source, expected):
    actual = generate_rewrite(Path("test.py"), dedent(source).strip())
    if isinstance(expected, str):
        expected = dedent(expected).strip()

    assert actual == expected
