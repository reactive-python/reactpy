from pathlib import Path

import pytest

import idom
from idom import Module
from tests.general_utils import patch_slots_object

HERE = Path(__file__).parent


def test_any_relative_or_abolute_url_allowed():
    Module("/absolute/url/module")
    Module("./relative/url/module")
    Module("../relative/url/module")
    Module("http://someurl.com/module")


def test_module_import_repr():
    assert (
        repr(Module("/absolute/url/module").declare("SomeComponent"))
        == "Import(name='SomeComponent', source='/absolute/url/module', fallback=None)"
    )


def test_module_does_not_exist():
    with pytest.raises(ValueError, match="is not installed or is not a URL"):
        Module("this-module-does-not-exist")


def test_installed_module(driver, display, victory):
    display(victory.VictoryBar)
    driver.find_element_by_class_name("VictoryContainer")


def test_reference_pre_installed_module(victory):
    assert victory.url == idom.Module("victory").url


def test_module_from_url():
    url = "https://code.jquery.com/jquery-3.5.0.js"
    jquery = idom.Module(url)
    assert jquery.url == url


def test_module_from_source(
    driver,
    driver_wait,
    display,
    htm,  # we need this in order to run the test js module
):
    test_module = Module("test-module", source_file=HERE / "test_js_module.js")

    response_data = idom.Ref(None)

    @idom.component
    def ShowButton():
        return test_module.TestButton(
            {
                "id": "test-button",
                "onClick": lambda event: response_data.set_current(event["data"]),
                "eventResponseData": 10,
            }
        )

    display(ShowButton)

    client_button = driver.find_element_by_id("test-button")
    client_button.click()
    driver_wait.until(lambda dvr: response_data.current == 10)


def test_module_checks_export_names(victory):
    with patch_slots_object(victory, "_export_names", []):
        with pytest.raises(ValueError, match="does not export"):
            victory.decalare("VictoryBar")
