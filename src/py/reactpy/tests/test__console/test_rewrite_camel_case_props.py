import sys
from pathlib import Path
from textwrap import dedent

import pytest
from click.testing import CliRunner

from reactpy._console.rewrite_camel_case_props import (
    generate_rewrite,
    rewrite_camel_case_props,
)

if sys.version_info < (3, 9):
    pytestmark = pytest.mark.skip(reason="ast.unparse is Python>=3.9")


def test_rewrite_camel_case_props_declarations(tmp_path):
    runner = CliRunner()

    tempfile: Path = tmp_path / "temp.py"
    tempfile.write_text("html.div(dict(camelCase='test'))")
    result = runner.invoke(
        rewrite_camel_case_props,
        args=[str(tmp_path)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert tempfile.read_text() == "html.div(dict(camel_case='test'))"


def test_rewrite_camel_case_props_declarations_no_files():
    runner = CliRunner()

    result = runner.invoke(
        rewrite_camel_case_props,
        args=["directory-does-no-exist"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0


@pytest.mark.parametrize(
    "source, expected",
    [
        (
            "html.div(dict(camelCase='test'))",
            "html.div(dict(camel_case='test'))",
        ),
        (
            "reactpy.html.button({'onClick': block_forever})",
            "reactpy.html.button({'on_click': block_forever})",
        ),
        (
            "html.div(dict(style={'testThing': test}))",
            "html.div(dict(style={'test_thing': test}))",
        ),
        (
            "html.div(dict(style=dict(testThing=test)))",
            "html.div(dict(style=dict(test_thing=test)))",
        ),
        (
            "vdom('tag', dict(camelCase='test'))",
            "vdom('tag', dict(camel_case='test'))",
        ),
        (
            "vdom('tag', dict(camelCase='test', **props))",
            "vdom('tag', dict(camel_case='test', **props))",
        ),
        (
            "html.div({'camelCase': test, 'data-thing': test})",
            "html.div({'camel_case': test, 'data-thing': test})",
        ),
        (
            "html.div({'camelCase': test, ignore: this})",
            "html.div({'camel_case': test, ignore: this})",
        ),
        # no rewrite
        (
            "html.div({'snake_case': test})",
            None,
        ),
        (
            "html.div({'data-case': test})",
            None,
        ),
        (
            "html.div(dict(snake_case='test'))",
            None,
        ),
        (
            "html.div()",
            None,
        ),
        (
            "vdom('tag')",
            None,
        ),
        (
            "html.div('child')",
            None,
        ),
        (
            "vdom('tag', 'child')",
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
