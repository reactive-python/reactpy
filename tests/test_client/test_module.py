from pathlib import Path

import pytest

import idom
from idom import Module
from idom.client.module import URL_SOURCE
from idom.config import IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT


HERE = Path(__file__).parent
JS_FIXTURES = HERE / "js"


@pytest.fixture
def victory():
    return idom.install("victory@35.4.0")


@pytest.fixture(scope="module")
def simple_button():
    return Module("simple-button", source_file=JS_FIXTURES / "simple-button.js")


def test_any_relative_or_abolute_url_allowed():
    Module("/absolute/url/module")
    Module("./relative/url/module")
    Module("../relative/url/module")
    Module("http://someurl.com/module")


def test_module_import_repr():
    assert (
        repr(Module("/absolute/url/module").declare("SomeComponent"))
        == "Import(name='SomeComponent', source='/absolute/url/module', sourceType='URL', fallback=None, exportsMount=False)"
    )


def test_install_multiple():
    # install several random JS packages
    pad_left, decamelize, is_sorted = idom.install(
        ["pad-left", "decamelize", "is-sorted"]
    )
    # ensure the output order is the same as the input order
    assert pad_left.source.endswith("pad-left")
    assert decamelize.source.endswith("decamelize")
    assert is_sorted.source.endswith("is-sorted")


def test_module_does_not_exist():
    with pytest.raises(ValueError, match="does not exist"):
        Module("this-module-does-not-exist")


def test_installed_module(driver, display, victory):
    display(victory.VictoryBar)
    driver.find_element_by_class_name("VictoryContainer")


def test_reference_pre_installed_module(victory):
    assert victory == idom.Module("victory")


def test_module_from_url():
    url = "https://code.jquery.com/jquery-3.5.0.js"
    jquery = idom.Module(url)
    assert jquery.source == url
    assert jquery.source_type == URL_SOURCE
    assert jquery.exports is None


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
            idom.Import(
                name="SomeComponent",
                source="https://some.url",
                source_type=URL_SOURCE,
                exports_mount=False,
            )
    finally:
        IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT.current = old_opt


def test_module_must_export_mount_if_exports_mount_is_set():
    with pytest.raises(ValueError, match="does not export 'mount'"):
        idom.Module(
            "component-without-mount",
            source_file=JS_FIXTURES / "component-without-mount.js",
            exports_mount=True,
        )


def test_cannot_have_source_file_for_url_source_type():
    with pytest.raises(ValueError, match="File given, but source type is 'URL'"):
        idom.Module("test", source_file="something.js", source_type=URL_SOURCE)


def test_cannot_check_exports_for_url_source_type():
    with pytest.raises(ValueError, match="Can't check exports for source type 'URL'"):
        idom.Module("test", check_exports=True, source_type=URL_SOURCE)


def test_invalid_source_type():
    with pytest.raises(ValueError, match="Invalid source type"):
        idom.Module("test", source_type="TYPE_DOES_NOT_EXIST")


def test_attribute_error_if_lowercase_name_doesn_not_exist():
    mod = idom.Module("test", source_type=URL_SOURCE)
    with pytest.raises(AttributeError, match="this_attribute_does_not_exist"):
        # This attribute would otherwise be considered to
        # be the name of a component the module exports.
        mod.this_attribute_does_not_exist
