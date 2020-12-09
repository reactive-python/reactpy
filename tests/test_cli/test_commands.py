import os
import json

from typer.testing import CliRunner

import idom
from idom.cli import main, settings
from idom.client.manage import web_module_exists, build_config


cli_runner = CliRunner()


def test_build_no_args():
    result = cli_runner.invoke(main, ["build"])
    assert result.exit_code == 0


def test_build_entrypoint(tmp_path):
    entrypoint_1 = tmp_path / "entrypoint_1.py"
    with entrypoint_1.open("w+") as f:
        f.write("idom_build_config = {'js_dependencies': ['jquery']}")

    result = cli_runner.invoke(main, ["build", "--entrypoint", str(entrypoint_1)])
    assert result.exit_code == 0
    assert web_module_exists("__main__", "jquery")

    entrypoint_2 = tmp_path / "entrypoint_2.py"
    entrypoint_2.touch()

    result = cli_runner.invoke(main, ["build", "--entrypoint", str(entrypoint_2)])
    assert result.exit_code == 0
    assert f"No build config found in {str(entrypoint_2)!r}" in result.stdout


def test_build_restore():
    result = cli_runner.invoke(main, ["build", "--restore"])
    assert result.exit_code == 0


def test_build_entrypoint_and_restore_are_mutually_exclusive():
    result = cli_runner.invoke(
        main, ["build", "--restore", "--entrypoint", "something.py"]
    )
    assert result.exit_code == 1
    assert "mutually exclusive" in result.stdout


def test_show_version():
    result = cli_runner.invoke(main, ["show", "version"])
    assert result.exit_code == 0
    assert idom.__version__ in result.stdout


def test_show_build_config():
    result = cli_runner.invoke(main, ["show", "build-config"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == build_config().data


def test_show_environment():
    result = cli_runner.invoke(main, ["show", "environment"])
    assert result.exit_code == 0
    shown = {}
    for line in result.stdout.split("\n"):
        if line.strip():
            name, value = line.split("=")
            shown[name] = value
    assert shown == {name: os.environ[name] for name in settings.NAMES}


def test_install():
    result = cli_runner.invoke(main, ["install", "jquery"])
    assert result.exit_code == 0
    assert build_config().has_entry("__main__")
    assert web_module_exists("__main__", "jquery")

    result = cli_runner.invoke(main, ["install", "lodash"])
    assert result.exit_code == 0
    assert build_config().has_entry("__main__")
    assert web_module_exists("__main__", "jquery")
    assert web_module_exists("__main__", "lodash")
