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
    yield Module("victory", install=True)


@pytest.mark.slow
def test_install(driver, display, victory):
    display(victory.Import("VictoryBar"))

    driver.find_element_by_class_name("VictoryContainer")

    assert client.web_module_exists("victory")
    assert client.web_module_url("victory") == "../web_modules/victory.js"


@pytest.mark.slow
def test_reference_pre_installed_module(victory):
    assert victory.url == idom.Module("victory").url


@pytest.mark.slow
def test_delete_module(victory):
    victory.delete()
    assert not client.web_module_exists("victory")

    with pytest.raises(ValueError, match="does not exist"):
        victory.delete()


@pytest.mark.slow
def test_custom_module(driver, display, victory):
    my_chart = Module("my/chart", source=HERE / "my_chart.js")

    assert client.web_module_exists("my/chart")
    assert client.web_module_url("my/chart") == "../web_modules/my/chart.js"

    display(my_chart.Import("Chart"))

    driver.find_element_by_class_name("VictoryContainer")

    my_chart.delete()

    assert not client.web_module_exists("my/chart")


def test_module_deletion():
    # also test install
    jquery = idom.Module("jquery", install="jquery@3.5.0")
    assert idom.client.web_module_exists(jquery.name)
    with idom.client.web_module_path(jquery.name).open() as f:
        assert "jQuery JavaScript Library v3.5.0" in f.read()
    jquery.delete()
    assert not idom.client.web_module_exists(jquery.name)


def test_module_from_url():
    url = "https://code.jquery.com/jquery-3.5.0.js"
    jquery = idom.Module(url)
    assert jquery.url == url
    with pytest.raises(ValueError, match="Module is not installed locally"):
        jquery.name
    with pytest.raises(ValueError, match="Module is not installed locally"):
        jquery.delete()
