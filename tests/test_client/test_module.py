import pytest
import idom
from idom import Module, client


def test_any_relative_or_abolute_url_allowed():
    Module("/absolute/url/module")
    Module("./relative/url/module")
    Module("../relative/url/module")
    Module("http://someurl.com/module")


@pytest.mark.slow
def test_installed_module(driver, display, victory_js):
    assert victory_js.installed
    display(victory_js.Import("VictoryBar"))
    driver.find_element_by_class_name("VictoryContainer")


@pytest.mark.slow
def test_reference_pre_installed_module(victory_js):
    assert victory_js.url == idom.Module("victory").url


def test_module_from_url():
    url = "https://code.jquery.com/jquery-3.5.0.js"
    jquery = idom.Module(url)
    assert jquery.url == url
    assert not jquery.installed


def test_module_uses_current_client_implementation():
    class MockClientImplementation:
        def web_module_url(self, source_name, package_name):
            return f"./mock/url/to/module-{package_name}.js"

        def web_module_exports(self, source_name, package_name):
            return ["x", "y", "z"]

        def web_module_exists(self, source_name, package_name):
            return package_name == "fake-name"

        def web_module_names(self):
            raise NotImplementedError()

        def web_module_path(self, package_name):
            raise NotImplementedError()

        def add_web_module(self, package_name, source):
            raise NotImplementedError()

    client.current = MockClientImplementation()

    fake = Module("fake-name")
    assert fake.url == "./mock/url/to/module-fake-name.js"
    assert fake.installed
    assert fake.exports == ["x", "y", "z"]
    assert fake.fallback is None

    with pytest.raises(ValueError, match="does not export 'DoesNotExist'"):
        fake.Import("DoesNotExist")
