import sys
from pathlib import Path
from textwrap import dedent

import pytest
from click.testing import CliRunner

from reactpy._console.rewrite_keys import generate_rewrite, rewrite_keys

if sys.version_info < (3, 9):
    pytestmark = pytest.mark.skip(reason="ast.unparse is Python>=3.9")


def test_rewrite_key_declarations(tmp_path):
    runner = CliRunner()

    tempfile: Path = tmp_path / "temp.py"
    tempfile.write_text("html.div(key='test')")
    result = runner.invoke(
        rewrite_keys,
        args=[str(tmp_path)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert tempfile.read_text() == "html.div({'key': 'test'})"


def test_rewrite_key_declarations_no_files():
    runner = CliRunner()

    result = runner.invoke(
        rewrite_keys,
        args=["directory-does-no-exist"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0


@pytest.mark.parametrize(
    "source, expected",
    [
        (
            "html.div(key='test')",
            "html.div({'key': 'test'})",
        ),
        (
            "html.div('something', key='test')",
            "html.div({'key': 'test'}, 'something')",
        ),
        (
            "html.div({'some_attr': 1}, child_1, child_2, key='test')",
            "html.div({'some_attr': 1, 'key': 'test'}, child_1, child_2)",
        ),
        (
            "vdom('div', key='test')",
            "vdom('div', {'key': 'test'})",
        ),
        (
            "vdom('div', 'something', key='test')",
            "vdom('div', {'key': 'test'}, 'something')",
        ),
        (
            "vdom('div', {'some_attr': 1}, child_1, child_2, key='test')",
            "vdom('div', {'some_attr': 1, 'key': 'test'}, child_1, child_2)",
        ),
        (
            "html.div(dict(some_attr=1), child_1, child_2, key='test')",
            "html.div(dict(some_attr=1, key='test'), child_1, child_2)",
        ),
        (
            "vdom('div', dict(some_attr=1), child_1, child_2, key='test')",
            "vdom('div', dict(some_attr=1, key='test'), child_1, child_2)",
        ),
        # avoid unnecessary changes
        (
            """
            def my_function():
                x = 1  # some comment
                return html.div(key='test')
            """,
            """
            def my_function():
                x = 1  # some comment
                return html.div({'key': 'test'})
            """,
        ),
        (
            """
            if condition:
                # some comment
                dom = html.div(key='test')
            """,
            """
            if condition:
                # some comment
                dom = html.div({'key': 'test'})
            """,
        ),
        (
            """
            [
                html.div(key='test'),
                html.div(key='test'),
            ]
            """,
            """
            [
                html.div({'key': 'test'}),
                html.div({'key': 'test'}),
            ]
            """,
        ),
        (
            """
            @deco(
                html.div(key='test'),
                html.div(key='test'),
            )
            def func():
                # comment
                x = [
                    1
                ]
            """,
            """
            @deco(
                html.div({'key': 'test'}),
                html.div({'key': 'test'}),
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
            @deco(html.div(key='test'), html.div(key='test'))
            def func():
                # comment
                x = [
                    1
                ]
            """,
            """
            @deco(html.div({'key': 'test'}), html.div({'key': 'test'}))
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
                else html.div(key='test')
            )
            """,
            """
            (
                result
                if condition
                else html.div({'key': 'test'})
            )
            """,
        ),
        # best effort to preserve comments
        (
            """
            x = 1
            html.div(
                "hello",
                # comment 1
                html.div(key='test'),
                # comment 2
                key='test',
            )
            """,
            """
            x = 1
            # comment 1
            # comment 2
            html.div({'key': 'test'}, 'hello', html.div({'key': 'test'}))
            """,
        ),
        # no rewrites
        (
            "html.no_an_element(key='test')",
            None,
        ),
        (
            "not_html.div(key='test')",
            None,
        ),
        (
            "html.div()",
            None,
        ),
        (
            "html.div(not_key='something')",
            None,
        ),
        (
            "vdom()",
            None,
        ),
        (
            "(some + expr)(key='test')",
            None,
        ),
        ("html.div()", None),
        # too ambiguous to rewrite
        (
            "html.div(child_1, child_2, key='test')",  # unclear if child_1 is attr dict
            None,
        ),
        (
            "vdom('div', child_1, child_2, key='test')",  # unclear if child_1 is attr dict
            None,
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
