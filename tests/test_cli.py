from typer.testing import CliRunner

import idom
from idom.cli import main
from idom.client.manage import web_module_exists

cli_runner = CliRunner()


def test_install():
    result = cli_runner.invoke(main, ["install", "jquery"])
    assert result.exit_code == 0
    assert web_module_exists("jquery")


def test_restore():
    result = cli_runner.invoke(main, ["restore"])
    assert result.exit_code == 0


def test_show_version():
    result = cli_runner.invoke(main, ["show", "version"])
    assert idom.__version__ in result.stdout
