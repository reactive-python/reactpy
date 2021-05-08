from pathlib import Path

import pytest

import idom
from idom import Module
from idom.config import IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT


HERE = Path(__file__).parent


@pytest.fixture
def victory():
    return idom.install("victory@35.4.0")


@pytest.fixture
def simple_button():
    return Module("simple-button", source_file=HERE / "js" / "simple-button.js")


def test_any_relative_or_abolute_url_allowed():
    Module("/absolute/url/module")
    Module("./relative/url/module")
    Module("../relative/url/module")
    Module("http://someurl.com/module")


def test_module_import_repr():
    assert (
        repr(Module("/absolute/url/module").declare("SomeComponent"))
        == "Import(name='SomeComponent', source='/absolute/url/module', fallback=None, hasMount=False)"
    )


def test_install_multiple():
    # install several random JS packages
    pad_left, decamelize, is_sorted = idom.install(
        ["pad-left", "decamelize", "is-sorted"]
    )
    # ensure the output order is the same as the input order
    assert pad_left.url.endswith("pad-left.js")
    assert decamelize.url.endswith("decamelize.js")
    assert is_sorted.url.endswith("is-sorted.js")


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


def test_module_from_source(driver, driver_wait, display, simple_button):
    response_data = idom.Ref(None)

    @idom.component
    def ShowButton():
        return simple_button.SimpleButton(
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


def test_module_checks_export_names(simple_button):
    with pytest.raises(ValueError, match="does not export 'ComponentDoesNotExist'"):
        simple_button.declare("ComponentDoesNotExist")


def test_idom_client_modules_must_have_mount():
    old_opt = IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT.current
    IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT.current = True
    try:
        with pytest.raises(RuntimeError, match="has no mount"):
            idom.Module("https://some.url", has_mount=False).SomeComponent
    finally:
        IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT.current = old_opt
