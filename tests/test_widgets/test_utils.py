from pathlib import Path

import pytest
import idom
from idom import client
from idom.widgets.utils import Module


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


def test_shared_hostwap(driver, display):
    """Ensure shared hotswapping works

    This basically means that previously rendered views of a hotswap element get updated
    when a new view is mounted, not just the next time it is re-displayed

    In this test we construct a scenario where clicking a button will cause a pre-existing
    hotswap element to be updated
    """

    @idom.element
    async def ButtonSwapsDivs():
        count = idom.Var(0)

        @idom.event
        async def on_click(event):
            count.value += 1
            mount(idom.html.div, {"id": f"hotswap-{count.value}"}, count.value)

        incr = idom.html.button({"onClick": on_click, "id": "incr-button"}, "incr")

        mount, make_hostswap = idom.widgets.hotswap(shared=True)
        mount(idom.html.div, {"id": f"hotswap-{count.value}"}, count.value)
        hotswap_view = make_hostswap()

        return idom.html.div(incr, hotswap_view)

    display(ButtonSwapsDivs)

    client_incr_button = driver.find_element_by_id("incr-button")

    driver.find_element_by_id("hotswap-0")
    client_incr_button.click()
    driver.find_element_by_id("hotswap-1")
    client_incr_button.click()
    driver.find_element_by_id("hotswap-2")
