from typer.testing import CliRunner

import idom
from idom.cli import main
from idom.client.manage import _private, web_module_exists


cli_runner = CliRunner()


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


def test_restore():
    assert cli_runner.invoke(main, ["restore"]).exit_code == 0


def test_show_version():
    terse_result = cli_runner.invoke(main, ["version"])
    assert idom.__version__ in terse_result.stdout

    verbose_result = cli_runner.invoke(main, ["version", "--verbose"])

    actual_rows = []
    for line in verbose_result.stdout.split("\n"):
        maybe_row = list(map(str.strip, filter(None, line.split("│"))))
        if len(maybe_row) > 1 and maybe_row != ["Package", "Version", "Language"]:
            actual_rows.append(maybe_row)

    expected_rows = [["idom", idom.__version__, "Python"]] + [
        [js_pkg, js_ver, "Javascript"]
        for js_pkg, js_ver in _private.build_dependencies().items()
    ]

    assert actual_rows == expected_rows
