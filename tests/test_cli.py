from typer.testing import CliRunner

import idom
from idom.cli import main
from idom.client.manage import web_module_exists
from idom.config import all_options


cli_runner = CliRunner()


def test_root():
    assert idom.__version__ in cli_runner.invoke(main, ["--version"]).stdout


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


def test_options():
    assert cli_runner.invoke(main, ["options"]).stdout.strip().split("\n") == [
        f"{opt.name} = {opt.current}"
        for opt in sorted(all_options(), key=lambda o: o.name)
    ]
