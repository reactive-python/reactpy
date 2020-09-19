from pathlib import Path

import pytest
import idom
from idom.client.manage import install, delete_web_modules
from idom import Module, client


HERE = Path(__file__).parent


@pytest.fixture
def victory():
    if "victory" not in client.installed():
        install(["victory"], [])
    return Module("victory")


def test_non_url_must_be_installed():
    with pytest.raises(ValueError, match="not installed"):
        Module("module/not/installed")


def test_any_relative_or_abolute_url_allowed():
    Module("/absolute/url/module")
    Module("./relative/url/module")
    Module("../relative/url/module")
    Module("http://someurl.com/module")


@pytest.mark.slow
def test_installed_module(driver, display, victory):
    assert victory.installed
    display(victory.Import("VictoryBar"))
    driver.find_element_by_class_name("VictoryContainer")


@pytest.mark.slow
def test_reference_pre_installed_module(victory):
    assert victory.url == idom.Module("victory").url


@pytest.mark.slow
def test_custom_module(driver, display, victory):
    my_chart = Module("my/chart", source_file=HERE / "my-chart.js")

    assert client.web_module_exists("my/chart")
    assert client.web_module_url("my/chart") == "../web_modules/my/chart.js"

    display(my_chart.Import("Chart"))

    driver.find_element_by_class_name("VictoryContainer")

    delete_web_modules("my/chart")
    assert not client.web_module_exists("my/chart")


def test_module_from_url():
    url = "https://code.jquery.com/jquery-3.5.0.js"
    jquery = idom.Module(url)
    assert jquery.url == url
    assert not jquery.installed


def test_module_uses_current_client_implementation():
    assert False
