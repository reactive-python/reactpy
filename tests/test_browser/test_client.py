from subprocess import CalledProcessError
from pathlib import Path
from unittest import mock

import pytest

from idom.widgets import Import, import_module
from idom import client

HERE = Path(__file__).parent


@pytest.fixture
def victory():
    yield Import("victory", install=True)


def test_install(driver, display, victory):
    display(victory.VictoryBar)

    driver.find_element_by_class_name("VictoryContainer")

    assert client.module_exists("web_modules", "victory")
    assert client.import_path("web_modules", "victory") == "../web_modules/victory.js"


def test_raise_on_missing_import_path():
    with pytest.raises(ValueError, match="does not exist"):
        client.import_path("web_modules", "module/that/does/not/exist")


def test_custom_module(driver, display, victory):
    my_chart = import_module("my_chart", HERE / "my_chart.js")

    display(my_chart.Chart)

    driver.find_element_by_class_name("VictoryContainer")

    assert client.module_exists("user_modules", "my_chart")
    assert (
        client.import_path("user_modules", "my_chart") == "../user_modules/my_chart.js"
    )


def test_delete_module(victory):
    client.delete_module("web_modules", "victory")
    assert not client.module_exists("web_modules", "victory")

    with pytest.raises(ValueError, match="does not exist"):
        client.delete_module("web_modules", "victory")


called_process_error = CalledProcessError(1, "failing-cmd")
called_process_error.stderr = b"an error occured"


@mock.patch("subprocess.run", side_effect=called_process_error)
def test_bad_subprocess_call(subprocess_run, caplog):
    with pytest.raises(CalledProcessError):
        client.install({"victory": "victory"})
    assert "an error occured" in caplog.text
