from pathlib import Path

import pytest
import idom
from idom import Module, install

HERE = Path(__file__).parent


def test_any_relative_or_abolute_url_allowed():
    Module("/absolute/url/module")
    Module("./relative/url/module")
    Module("../relative/url/module")
    Module("http://someurl.com/module")


def test_module_import_repr():
    assert (
        repr(Module("/absolute/url/module").define("SomeComponent"))
        == "Import(name='SomeComponent', source='/absolute/url/module', fallback=None)"
    )


def test_module_does_not_exist():
    with pytest.raises(ValueError, match="is not installed or is not a URL"):
        Module("this-module-does-not-exist")


def test_installed_module(driver, display, victory):
    display(victory.define("VictoryBar"))
    driver.find_element_by_class_name("VictoryContainer")


def test_install_checks_client_implementation(client_implementation):
    class MockClientImplementation:
        def web_module_names(self):
            return set()

    client_implementation.current = MockClientImplementation()

    with pytest.raises(
        RuntimeError,
        match=r"Successfuly installed .* but client implementation .* failed to discover .*",
    ):
        install("jquery@3.5.0", ignore_installed=True)


def test_reference_pre_installed_module(victory):
    assert victory.url == idom.Module("victory").url


def test_module_from_url():
    url = "https://code.jquery.com/jquery-3.5.0.js"
    jquery = idom.Module(url)
    assert jquery.url == url


def test_module_uses_current_client_implementation(client_implementation):
    class MockClientImplementation:
        def web_module_url(self, package_name):
            return f"./mock/url/to/module-{package_name}.js"

        def web_module_exports(self, package_name):
            return ["x", "y", "z"]

        def web_module_exists(self, package_name):
            return package_name == "fake-name"

        def web_module_names(self):
            raise NotImplementedError()

        def web_module_path(self, package_name):
            raise NotImplementedError()

        def add_web_module(self, package_name, source):
            raise NotImplementedError()

    client_implementation.current = MockClientImplementation()

    fake = Module("fake-name")
    assert fake.url == "./mock/url/to/module-fake-name.js"
    assert fake.exports == ["x", "y", "z"]
    assert fake.fallback is None

    with pytest.raises(ValueError, match="does not export 'DoesNotExist'"):
        fake.define("DoesNotExist")

    for name in fake.exports:
        fake.define(name)


def test_module_from_source(driver, driver_wait, display):
    test_module = Module("test-module", source_file=HERE / "test_js_module.js")
    test_button = test_module.define("TestButton")

    response_data = idom.Ref(None)

    @idom.element
    def ShowButton():
        return test_button(
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
