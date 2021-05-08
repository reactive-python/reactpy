from unittest.mock import patch

from rich.console import Console
from typer.testing import CliRunner

import idom
from idom.cli import main
from idom.client.manage import _private, web_module_exists
from idom.config import IDOM_CLIENT_BUILD_DIR


cli_runner = CliRunner()


with_large_console = patch("idom.cli.console", Console(width=10000))


def assert_rich_table_equals(stdout, expected_header, expected_rows):
    parsed_lines = []
    for line in stdout.split("\n"):
        maybe_row = list(
            map(str.strip, filter(None, line.replace("┃", "│").split("│")))
        )
        if len(maybe_row) > 1:
            parsed_lines.append(maybe_row)

    actual_header, *actual_rows = parsed_lines

    assert actual_header == expected_header and actual_rows == expected_rows


@with_large_console
def test_install():
    cli_runner.invoke(main, ["restore"])
    assert cli_runner.invoke(main, ["install", "jquery"]).exit_code == 0
    assert web_module_exists("jquery")

    result = cli_runner.invoke(main, ["install", "jquery"])
    print(result.stdout)
    assert result.exit_code == 0
    assert "Already installed ['jquery']" in result.stdout
    assert "Build skipped" in result.stdout
    assert web_module_exists("jquery")


@with_large_console
def test_restore():
    assert cli_runner.invoke(main, ["restore"]).exit_code == 0


@with_large_console
def test_show_version():
    terse_result = cli_runner.invoke(main, ["version"])
    assert idom.__version__ in terse_result.stdout

    verbose_result = cli_runner.invoke(main, ["version", "--verbose"])

    assert_rich_table_equals(
        verbose_result.stdout,
        ["Package", "Version", "Language"],
        (
            [["idom", idom.__version__, "Python"]]
            + [
                [js_pkg, js_ver, "Javascript"]
                for js_pkg, js_ver in _private.build_dependencies().items()
            ]
        ),
    )


@with_large_console
def test_show_options():
    build_dir = str(IDOM_CLIENT_BUILD_DIR.get())
    assert_rich_table_equals(
        cli_runner.invoke(main, ["options"]).stdout,
        ["Name", "Value", "Default", "Mutable"],
        [
            ["IDOM_CLIENT_BUILD_DIR", build_dir, build_dir, "True"],
            ["IDOM_CLIENT_IMPORT_SOURCE_URL", "/client", "/client", "True"],
            ["IDOM_DEBUG_MODE", "False", "False", "False"],
            ["IDOM_FEATURE_INDEX_AS_DEFAULT_KEY", "False", "False", "False"],
        ],
    )
