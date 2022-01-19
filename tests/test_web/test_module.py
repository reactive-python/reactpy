from pathlib import Path

import pytest
from sanic import Sanic
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

import idom
from idom.server.sanic import PerClientStateServer
from idom.testing import ServerMountPoint, assert_idom_did_not_log, assert_idom_logged
from idom.web.module import NAME_SOURCE, WebModule


JS_FIXTURES_DIR = Path(__file__).parent / "js_fixtures"


def test_that_js_module_unmount_is_called(driver, display):
    SomeComponent = idom.web.export(
        idom.web.module_from_file(
            "set-flag-when-unmount-is-called",
            JS_FIXTURES_DIR / "set-flag-when-unmount-is-called.js",
        ),
        "SomeComponent",
    )

    set_current_component = idom.Ref(None)

    @idom.component
    def ShowCurrentComponent():
        current_component, set_current_component.current = idom.hooks.use_state(
            lambda: SomeComponent({"id": "some-component", "text": "initial component"})
        )
        return current_component

    display(ShowCurrentComponent)

    driver.find_element("id", "some-component")

    set_current_component.current(
        idom.html.h1({"id": "some-other-component"}, "some other component")
    )

    # the new component has been displayed
    driver.find_element("id", "some-other-component")

    # the unmount callback for the old component was called
    driver.find_element("id", "unmount-flag")


def test_module_from_url(driver):
    app = Sanic(__name__)

    # instead of directing the URL to a CDN, we just point it to this static file
    app.static(
        "/simple-button.js",
        str(JS_FIXTURES_DIR / "simple-button.js"),
        content_type="text/javascript",
    )

    SimpleButton = idom.web.export(
        idom.web.module_from_url("/simple-button.js", resolve_exports=False),
        "SimpleButton",
    )

    @idom.component
    def ShowSimpleButton():
        return SimpleButton({"id": "my-button"})

    with ServerMountPoint(PerClientStateServer, app=app) as mount_point:
        mount_point.mount(ShowSimpleButton)
        driver.get(mount_point.url())
        driver.find_element("id", "my-button")


def test_module_from_template_where_template_does_not_exist():
    with pytest.raises(ValueError, match="No template for 'does-not-exist.js'"):
        idom.web.module_from_template("does-not-exist", "something.js")


def test_module_from_template(driver, display):
    victory = idom.web.module_from_template("react", "victory-bar@35.4.0")
    VictoryBar = idom.web.export(victory, "VictoryBar")
    display(VictoryBar)
    wait = WebDriverWait(driver, 10)
    wait.until(
        expected_conditions.visibility_of_element_located(
            (By.CLASS_NAME, "VictoryContainer")
        )
    )


def test_module_from_file(driver, driver_wait, display):
    SimpleButton = idom.web.export(
        idom.web.module_from_file(
            "simple-button", JS_FIXTURES_DIR / "simple-button.js"
        ),
        "SimpleButton",
    )

    is_clicked = idom.Ref(False)

    @idom.component
    def ShowSimpleButton():
        return SimpleButton(
            {"id": "my-button", "onClick": lambda event: is_clicked.set_current(True)}
        )

    display(ShowSimpleButton)

    button = driver.find_element("id", "my-button")
    button.click()
    driver_wait.until(lambda d: is_clicked.current)


def test_module_from_file_source_conflict(tmp_path):
    first_file = tmp_path / "first.js"

    with pytest.raises(FileNotFoundError, match="does not exist"):
        idom.web.module_from_file("temp", first_file)

    first_file.touch()

    idom.web.module_from_file("temp", first_file)

    second_file = tmp_path / "second.js"
    second_file.touch()

    # ok, same content
    idom.web.module_from_file("temp", second_file)

    third_file = tmp_path / "third.js"
    third_file.write_text("something-different")

    with assert_idom_logged(r"Existing web module .* will be replaced with"):
        idom.web.module_from_file("temp", third_file)


def test_web_module_from_file_symlink(tmp_path):
    file = tmp_path / "temp.js"
    file.touch()

    module = idom.web.module_from_file("temp", file, symlink=True)

    assert module.file.resolve().read_text() == ""

    file.write_text("hello world!")

    assert module.file.resolve().read_text() == "hello world!"


def test_web_module_from_file_symlink_twice(tmp_path):
    file_1 = tmp_path / "temp_1.js"
    file_1.touch()

    idom.web.module_from_file("temp", file_1, symlink=True)

    with assert_idom_did_not_log(r"Existing web module .* will be replaced with"):
        idom.web.module_from_file("temp", file_1, symlink=True)

    file_2 = tmp_path / "temp_2.js"
    file_2.write_text("something")

    with assert_idom_logged(r"Existing web module .* will be replaced with"):
        idom.web.module_from_file("temp", file_2, symlink=True)


def test_web_module_from_file_replace_existing(tmp_path):
    file1 = tmp_path / "temp1.js"
    file1.touch()

    idom.web.module_from_file("temp", file1)

    file2 = tmp_path / "temp2.js"
    file2.write_text("something")

    with assert_idom_logged(r"Existing web module .* will be replaced with"):
        idom.web.module_from_file("temp", file2)


def test_module_missing_exports():
    module = WebModule("test", NAME_SOURCE, None, {"a", "b", "c"}, None, False)

    with pytest.raises(ValueError, match="does not export 'x'"):
        idom.web.export(module, "x")

    with pytest.raises(ValueError, match=r"does not export \['x', 'y'\]"):
        idom.web.export(module, ["x", "y"])


def test_module_exports_multiple_components(driver, display):
    Header1, Header2 = idom.web.export(
        idom.web.module_from_file(
            "exports-two-components", JS_FIXTURES_DIR / "exports-two-components.js"
        ),
        ["Header1", "Header2"],
    )

    display(lambda: Header1({"id": "my-h1"}, "My Header 1"))

    driver.find_element("id", "my-h1")

    display(lambda: Header2({"id": "my-h2"}, "My Header 2"))

    driver.find_element("id", "my-h2")


def test_imported_components_can_render_children(driver, display):
    module = idom.web.module_from_file(
        "component-can-have-child", JS_FIXTURES_DIR / "component-can-have-child.js"
    )
    Parent, Child = idom.web.export(module, ["Parent", "Child"])

    display(
        lambda: Parent(
            Child({"index": 1}),
            Child({"index": 2}),
            Child({"index": 3}),
        )
    )

    parent = driver.find_element("id", "the-parent")
    children = parent.find_elements("tag name", "li")

    assert len(children) == 3

    for index, child in enumerate(children):
        assert child.get_attribute("id") == f"child-{index + 1}"


def test_module_from_string():
    idom.web.module_from_string("temp", "old")
    with assert_idom_logged(r"Existing web module .* will be replaced with"):
        idom.web.module_from_string("temp", "new")
