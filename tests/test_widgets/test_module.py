from pathlib import Path

import pytest
import idom
from idom import client
from idom import Module


HERE = Path(__file__).parent


def test_module_cannot_have_source_and_install():
    with pytest.raises(ValueError, match=r"Both .* were given."):
        idom.Module("something", install="something", source=HERE / "something.js")


@pytest.fixture
def victory():
    if "victory" not in client.installed():
        client.install(["victory"], [])
    return Module("victory")


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
    my_chart = Module("my/chart", source=HERE / "my_chart.js")

    assert client.web_module_exists("my/chart")
    assert client.web_module_url("my/chart") == "../web_modules/my/chart.js"

    display(my_chart.Import("Chart"))

    driver.find_element_by_class_name("VictoryContainer")

    my_chart.delete()

    assert not client.web_module_exists("my/chart")


def test_module_from_url():
    url = "https://code.jquery.com/jquery-3.5.0.js"
    jquery = idom.Module(url)
    assert jquery.url == url
    assert not jquery.installed
