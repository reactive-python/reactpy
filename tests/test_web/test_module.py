from pathlib import Path

import pytest
from servestatic import ServeStaticASGI

import reactpy
from reactpy.executors.asgi.standalone import ReactPy
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
    SimpleButton = reactpy.web.export(
        reactpy.web.module_from_url("/static/simple-button.js", resolve_exports=False),
        "SimpleButton",
    )

    @reactpy.component
    def ShowSimpleButton():
        return SimpleButton({"id": "my-button"})

    app = ReactPy(ShowSimpleButton)
    app = ServeStaticASGI(app, JS_FIXTURES_DIR, "/static/")

    async with BackendFixture(app) as server:
        async with DisplayFixture(server, browser) as display:
            await display.show(ShowSimpleButton)

            await display.page.wait_for_selector("#my-button")


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


async def test_keys_properly_propagated(display: DisplayFixture):
    """
    Fix https://github.com/reactive-python/reactpy/issues/1275

    The `key` property was being lost in its propagation from the server-side ReactPy
    definition to the front-end JavaScript.

    This property is required for certain JS components, such as the GridLayout from
    react-grid-layout.
    """
    module = reactpy.web.module_from_file(
        "keys-properly-propagated", JS_FIXTURES_DIR / "keys-properly-propagated.js"
    )
    GridLayout = reactpy.web.export(module, "GridLayout")

    await display.show(
        lambda: GridLayout({
            "layout": [
                {
                    "i": "a",
                    "x": 0,
                    "y": 0,
                    "w": 1,
                    "h": 2,
                    "static": True,
                },
                {
                    "i": "b",
                    "x": 1,
                    "y": 0,
                    "w": 3,
                    "h": 2,
                    "minW": 2,
                    "maxW": 4,
                },
                {
                    "i": "c",
                    "x": 4,
                    "y": 0,
                    "w": 1,
                    "h": 2,
                }
            ],
            "cols": 12,
            "rowHeight": 30,
            "width": 1200,
        },
            reactpy.html.div({"key": "a"}, "a"),
            reactpy.html.div({"key": "b"}, "b"),
            reactpy.html.div({"key": "c"}, "c"),
        )
    )

    parent = await display.page.wait_for_selector(".react-grid-layout", state="attached")
    children = await parent.query_selector_all("div")

    # The children simply will not render unless they receive the key prop
    assert len(children) == 3


async def test_subcomponent_notation_as_str_attrs(display: DisplayFixture):
    module = reactpy.web.module_from_file(
        "subcomponent-notation", JS_FIXTURES_DIR / "subcomponent-notation.js",
    )
    InputGroup, InputGroupText, FormControl, FormLabel = reactpy.web.export(
        module,
        ["InputGroup", "InputGroup.Text", "Form.Control", "Form.Label"]
    )

    content = reactpy.html.div({"id": "the-parent"},
        InputGroup(
            InputGroupText({"id": "basic-addon1"}, "@"),
            FormControl({
                "placeholder": "Username",
                "aria-label": "Username",
                "aria-describedby": "basic-addon1",
            }),
        ),

        InputGroup(
            FormControl({
                "placeholder": "Recipient's username",
                "aria-label": "Recipient's username",
                "aria-describedby": "basic-addon2",
            }),
            InputGroupText({"id": "basic-addon2"}, "@example.com"),
        ),

        FormLabel({"htmlFor": "basic-url"}, "Your vanity URL"),
        InputGroup(
            InputGroupText({"id": "basic-addon3"},
                "https://example.com/users/"
            ),
            FormControl({"id": "basic-url", "aria-describedby": "basic-addon3"}),
        ),

        InputGroup(
            InputGroupText("$"),
            FormControl({"aria-label": "Amount (to the nearest dollar)"}),
            InputGroupText(".00"),
        ),

        InputGroup(
            InputGroupText("With textarea"),
            FormControl({"as": "textarea", "aria-label": "With textarea"}),
        )
    )

    await display.show(
        lambda: content
    )

    parent = await display.page.wait_for_selector("#the-parent", state="visible")
    input_group_text = await parent.query_selector_all(".input-group-text")
    form_control = await parent.query_selector_all(".form-control")
    form_label = await parent.query_selector_all(".form-label")

    assert len(input_group_text) == 6
    assert len(form_control) == 5
    assert len(form_label) == 1


async def test_subcomponent_notation_as_obj_attrs(display: DisplayFixture):
    module = reactpy.web.module_from_file(
        "subcomponent-notation", JS_FIXTURES_DIR / "subcomponent-notation.js",
    )
    InputGroup, Form = reactpy.web.export(module, ["InputGroup", "Form"])

    content = reactpy.html.div({"id": "the-parent"},
        InputGroup(
            InputGroup.Text({"id": "basic-addon1"}, "@"),
            Form.Control({
                "placeholder": "Username",
                "aria-label": "Username",
                "aria-describedby": "basic-addon1",
            }),
        ),

        InputGroup(
            Form.Control({
                "placeholder": "Recipient's username",
                "aria-label": "Recipient's username",
                "aria-describedby": "basic-addon2",
            }),
            InputGroup.Text({"id": "basic-addon2"}, "@example.com"),
        ),

        Form.Label({"htmlFor": "basic-url"}, "Your vanity URL"),
        InputGroup(
            InputGroup.Text({"id": "basic-addon3"},
                "https://example.com/users/"
            ),
            Form.Control({"id": "basic-url", "aria-describedby": "basic-addon3"}),
        ),

        InputGroup(
            InputGroup.Text("$"),
            Form.Control({"aria-label": "Amount (to the nearest dollar)"}),
            InputGroup.Text(".00"),
        ),

        InputGroup(
            InputGroup.Text("With textarea"),
            Form.Control({"as": "textarea", "aria-label": "With textarea"}),
        )
    )

    await display.show(
        lambda: content
    )

    parent = await display.page.wait_for_selector("#the-parent", state="visible")
    input_group_text = await parent.query_selector_all(".input-group-text")
    form_control = await parent.query_selector_all(".form-control")
    form_label = await parent.query_selector_all(".form-label")

    assert len(input_group_text) == 6
    assert len(form_control) == 5
    assert len(form_label) == 1


def test_module_from_string():
    reactpy.web.module_from_string("temp", "old")
    with assert_reactpy_did_log(r"Existing web module .* will be replaced with"):
        reactpy.web.module_from_string("temp", "new")
