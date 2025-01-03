from pathlib import Path

import pytest
from sanic import Sanic

import reactpy
from reactpy.backend import sanic as sanic_implementation
from reactpy.testing import (
    BackendFixture,
    DisplayFixture,
    assert_reactpy_did_log,
    assert_reactpy_did_not_log,
    poll,
)
from reactpy.web.module import NAME_SOURCE, WebModule

JS_FIXTURES_DIR = Path(__file__).parent / "js_fixtures"


async def test_that_js_module_unmount_is_called(display: DisplayFixture):
    SomeComponent = reactpy.web.export(
        reactpy.web.module_from_file(
            "set-flag-when-unmount-is-called",
            JS_FIXTURES_DIR / "set-flag-when-unmount-is-called.js",
        ),
        "SomeComponent",
    )

    set_current_component = reactpy.Ref(None)

    @reactpy.component
    def ShowCurrentComponent():
        current_component, set_current_component.current = reactpy.hooks.use_state(
            lambda: SomeComponent({"id": "some-component", "text": "initial component"})
        )
        return current_component

    await display.show(ShowCurrentComponent)

    await display.page.wait_for_selector("#some-component", state="attached")

    set_current_component.current(
        reactpy.html.h1({"id": "some-other-component"}, "some other component")
    )

    # the new component has been displayed
    await display.page.wait_for_selector("#some-other-component", state="attached")

    # the unmount callback for the old component was called
    await display.page.wait_for_selector("#unmount-flag", state="attached")


async def test_module_from_url(browser):
    app = Sanic("test_module_from_url")

    # instead of directing the URL to a CDN, we just point it to this static file
    app.static(
        "/simple-button.js",
        str(JS_FIXTURES_DIR / "simple-button.js"),
        content_type="text/javascript",
    )

    SimpleButton = reactpy.web.export(
        reactpy.web.module_from_url("/simple-button.js", resolve_exports=False),
        "SimpleButton",
    )

    @reactpy.component
    def ShowSimpleButton():
        return SimpleButton({"id": "my-button"})

    async with BackendFixture(app=app, implementation=sanic_implementation) as server:
        async with DisplayFixture(server, browser) as display:
            await display.show(ShowSimpleButton)

            await display.page.wait_for_selector("#my-button")


def test_module_from_template_where_template_does_not_exist():
    with pytest.raises(ValueError, match="No template for 'does-not-exist.js'"):
        reactpy.web.module_from_template("does-not-exist", "something.js")


async def test_module_from_template(display: DisplayFixture):
    victory = reactpy.web.module_from_template("react@18.2.0", "victory-bar@35.4.0")

    assert "react@18.2.0" in victory.file.read_text()
    VictoryBar = reactpy.web.export(victory, "VictoryBar")
    await display.show(VictoryBar)

    await display.page.wait_for_selector(".VictoryContainer")


async def test_module_from_file(display: DisplayFixture):
    SimpleButton = reactpy.web.export(
        reactpy.web.module_from_file(
            "simple-button", JS_FIXTURES_DIR / "simple-button.js"
        ),
        "SimpleButton",
    )

    is_clicked = reactpy.Ref(False)

    @reactpy.component
    def ShowSimpleButton():
        return SimpleButton(
            {"id": "my-button", "onClick": lambda event: is_clicked.set_current(True)}
        )

    await display.show(ShowSimpleButton)

    button = await display.page.wait_for_selector("#my-button")
    await button.click()
    await poll(lambda: is_clicked.current).until_is(True)


def test_module_from_file_source_conflict(tmp_path):
    first_file = tmp_path / "first.js"

    with pytest.raises(FileNotFoundError, match="does not exist"):
        reactpy.web.module_from_file("temp", first_file)

    first_file.touch()

    reactpy.web.module_from_file("temp", first_file)

    second_file = tmp_path / "second.js"
    second_file.touch()

    # ok, same content
    reactpy.web.module_from_file("temp", second_file)

    third_file = tmp_path / "third.js"
    third_file.write_text("something-different")

    with assert_reactpy_did_log(r"Existing web module .* will be replaced with"):
        reactpy.web.module_from_file("temp", third_file)


def test_web_module_from_file_symlink(tmp_path):
    file = tmp_path / "temp.js"
    file.touch()

    module = reactpy.web.module_from_file("temp", file, symlink=True)

    assert module.file.resolve().read_text() == ""

    file.write_text("hello world!")

    assert module.file.resolve().read_text() == "hello world!"


def test_web_module_from_file_symlink_twice(tmp_path):
    file_1 = tmp_path / "temp_1.js"
    file_1.touch()

    reactpy.web.module_from_file("temp", file_1, symlink=True)

    with assert_reactpy_did_not_log(r"Existing web module .* will be replaced with"):
        reactpy.web.module_from_file("temp", file_1, symlink=True)

    file_2 = tmp_path / "temp_2.js"
    file_2.write_text("something")

    with assert_reactpy_did_log(r"Existing web module .* will be replaced with"):
        reactpy.web.module_from_file("temp", file_2, symlink=True)


def test_web_module_from_file_replace_existing(tmp_path):
    file1 = tmp_path / "temp1.js"
    file1.touch()

    reactpy.web.module_from_file("temp", file1)

    file2 = tmp_path / "temp2.js"
    file2.write_text("something")

    with assert_reactpy_did_log(r"Existing web module .* will be replaced with"):
        reactpy.web.module_from_file("temp", file2)


def test_module_missing_exports():
    module = WebModule("test", NAME_SOURCE, None, {"a", "b", "c"}, None, False)

    with pytest.raises(ValueError, match="does not export 'x'"):
        reactpy.web.export(module, "x")

    with pytest.raises(ValueError, match=r"does not export \['x', 'y'\]"):
        reactpy.web.export(module, ["x", "y"])


async def test_module_exports_multiple_components(display: DisplayFixture):
    Header1, Header2 = reactpy.web.export(
        reactpy.web.module_from_file(
            "exports-two-components", JS_FIXTURES_DIR / "exports-two-components.js"
        ),
        ["Header1", "Header2"],
    )

    await display.show(lambda: Header1({"id": "my-h1"}, "My Header 1"))

    await display.page.wait_for_selector("#my-h1", state="attached")

    await display.show(lambda: Header2({"id": "my-h2"}, "My Header 2"))

    await display.page.wait_for_selector("#my-h2", state="attached")


async def test_imported_components_can_render_children(display: DisplayFixture):
    module = reactpy.web.module_from_file(
        "component-can-have-child", JS_FIXTURES_DIR / "component-can-have-child.js"
    )
    Parent, Child = reactpy.web.export(module, ["Parent", "Child"])

    await display.show(
        lambda: Parent(
            Child({"index": 1}),
            Child({"index": 2}),
            Child({"index": 3}),
        )
    )

    parent = await display.page.wait_for_selector("#the-parent", state="attached")
    children = await parent.query_selector_all("li")

    assert len(children) == 3

    for index, child in enumerate(children):
        assert (await child.get_attribute("id")) == f"child-{index + 1}"


def test_module_from_string():
    reactpy.web.module_from_string("temp", "old")
    with assert_reactpy_did_log(r"Existing web module .* will be replaced with"):
        reactpy.web.module_from_string("temp", "new")
