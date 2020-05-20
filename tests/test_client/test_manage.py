from subprocess import CalledProcessError
from pathlib import Path
from unittest import mock

import pytest

from idom import Module
from idom import client

HERE = Path(__file__).parent


@pytest.fixture
def victory():
    yield Module("victory", install=True)


@pytest.mark.slow
def test_install(driver, display, victory):
    display(victory.Import("VictoryBar"))

    driver.find_element_by_class_name("VictoryContainer")

    assert client.web_module_exists("victory")
    assert client.web_module("victory") == "../web_modules/victory.js"


def test_raise_on_missing_import_path():
    with pytest.raises(ValueError, match="does not exist"):
        client.web_module("module/that/does/not/exist")


@pytest.mark.slow
def test_custom_module(driver, display, victory):
    with open(HERE / "my_chart.js") as f:
        my_chart = Module("my/chart", source=f)

    assert client.web_module_exists("my/chart")
    assert client.web_module("my/chart") == "../web_modules/my/chart.js"

    display(my_chart.Import("Chart"))

    driver.find_element_by_class_name("VictoryContainer")


@pytest.mark.slow
def test_delete_module(victory):
    victory.delete()
    assert not client.web_module_exists("victory")

    with pytest.raises(ValueError, match="does not exist"):
        victory.delete()


called_process_error = CalledProcessError(1, "failing-cmd")
called_process_error.stderr = b"an error occured"


@mock.patch("subprocess.run", side_effect=called_process_error)
def test_bad_subprocess_call(subprocess_run, caplog):
    with pytest.raises(CalledProcessError):
        client.install({"victory": "victory"})
    assert "an error occured" in caplog.text
