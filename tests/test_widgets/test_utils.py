from io import StringIO

import pytest
import idom


def test_module_cannot_have_source_and_install():
    with pytest.raises(ValueError, match=r"Both .* were given."):
        idom.Module("something", install="something", source=StringIO())


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
    async def ButtonSwapsDivs(self):
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
