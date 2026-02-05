import pytest
from playwright.async_api import expect

import reactpy
from reactpy import html
from reactpy.reactjs import component_from_npm, import_reactjs
from reactpy.testing import GITHUB_ACTIONS, BackendFixture, DisplayFixture

MISSING_IMPORT_MAP_MSG = "ReactPy did not detect a suitable JavaScript import map"


@pytest.fixture(scope="module")
async def display(browser):
    """Override for the display fixture that includes ReactJS imports."""
    async with BackendFixture(html_head=html.head(import_reactjs("react"))) as backend:
        async with DisplayFixture(backend=backend, browser=browser) as new_display:
            yield new_display


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_react_bootstrap(display: DisplayFixture, caplog):
    Button = component_from_npm("react-bootstrap", "Button", version="2")

    @reactpy.component
    def App():
        return Button({"variant": "primary", "id": "test-button"}, "Click me")

    await display.show(App)

    button = display.page.locator("#test-button")
    await expect(button).to_have_text("Click me")

    # Check if it has the correct class for primary variant
    # React Bootstrap buttons usually have 'btn' and 'btn-primary' classes
    await expect(button).to_contain_class("btn")
    await expect(button).to_contain_class("btn-primary")

    # Ensure missing import map was NOT logged
    assert MISSING_IMPORT_MAP_MSG not in " ".join(x.msg for x in caplog.records)


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_react_bootstrap_with_local_framework(browser, caplog):
    Button = component_from_npm("react-bootstrap", "Button", version="2")

    @reactpy.component
    def App():
        return Button({"variant": "primary", "id": "test-button"}, "Click me")

    async with BackendFixture(
        html_head=html.head(import_reactjs(use_local=True))
    ) as backend:
        async with DisplayFixture(backend=backend, browser=browser) as display:
            await display.show(App)

            button = display.page.locator("#test-button")
            await expect(button).to_have_text("Click me")

            # Check if it has the correct class for primary variant
            # React Bootstrap buttons usually have 'btn' and 'btn-primary' classes
            await expect(button).to_contain_class("btn")
            await expect(button).to_contain_class("btn-primary")

            # Ensure missing import map was NOT logged
            assert MISSING_IMPORT_MAP_MSG not in " ".join(x.msg for x in caplog.records)


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_without_explicit_reactjs_import(browser, caplog):
    Button = component_from_npm("react-bootstrap", "Button", version="2")

    @reactpy.component
    def App():
        return Button({"variant": "primary", "id": "test-button"}, "Click me")

    async with BackendFixture() as backend:
        async with DisplayFixture(backend=backend, browser=browser) as display:
            await display.show(App)

            button = display.page.locator("#test-button")
            await expect(button).to_have_text("Click me")

            # Check if it has the correct class for primary variant
            # React Bootstrap buttons usually have 'btn' and 'btn-primary' classes
            await expect(button).to_contain_class("btn")
            await expect(button).to_contain_class("btn-primary")

            # Check if missing import map was logged
            assert MISSING_IMPORT_MAP_MSG in " ".join(x.msg for x in caplog.records)


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_material_ui(display: DisplayFixture):
    Button = component_from_npm("@mui/material", "Button", version="7")

    @reactpy.component
    def App():
        return Button({"variant": "contained", "id": "test-button"}, "Click me")

    await display.show(App)
    button = display.page.locator("#test-button")
    # Material UI transforms text to uppercase by default
    await expect(button).to_have_text("Click me")
    await expect(button).to_have_css("text-transform", "uppercase")
    await expect(button).to_contain_class("MuiButton-root")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_antd(display: DisplayFixture):
    Button = component_from_npm("antd", "Button", version="6")

    @reactpy.component
    def App():
        return Button({"type": "primary", "id": "test-button"}, "Click me")

    await display.show(App)
    button = display.page.locator("#test-button")
    await expect(button).to_have_text("Click me")
    await expect(button).to_contain_class("ant-btn")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_chakra_ui(display: DisplayFixture):
    ChakraProvider, _, Button = _get_chakra_components()

    @reactpy.component
    def App():
        return ChakraProvider(
            Button({"colorScheme": "blue", "id": "test-button"}, "Click me")
        )

    await display.show(App)
    button = display.page.locator("#test-button")
    await expect(button).to_have_text("Click me")
    await expect(button).to_contain_class("chakra-button")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_semantic_ui_react(browser):
    # Semantic UI is deprecated and doesn't get updates. Thus, it is incompatible with the
    # latest React versions. We use this as an opportunity to test Preact here.
    Button = component_from_npm("semantic-ui-react", "Button", version="2")

    @reactpy.component
    def App():
        return html._(
            Button({"primary": True, "id": "test-button"}, "Click me"),
        )

    async with BackendFixture(html_head=html.head(import_reactjs("preact"))) as backend:
        async with DisplayFixture(backend=backend, browser=browser) as display:
            await display.show(App)
            button = display.page.locator("#test-button")
            await expect(button).to_have_text("Click me")
            await expect(button).to_contain_class("ui")
            await expect(button).to_contain_class("button")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_mantine(display: DisplayFixture):
    MantineProvider, Button = component_from_npm(
        "@mantine/core", ["MantineProvider", "Button"], version="8"
    )

    @reactpy.component
    def App():
        return MantineProvider(Button({"id": "test-button"}, "Click me"))

    await display.show(App)
    button = display.page.locator("#test-button")
    await expect(button).to_have_text("Click me")
    await expect(button).to_contain_class("mantine-Button-root")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_fluent_ui(display: DisplayFixture):
    PrimaryButton = component_from_npm("@fluentui/react", "PrimaryButton", version="8")

    @reactpy.component
    def App():
        return PrimaryButton({"id": "test-button"}, "Click me")

    await display.show(App)
    button = display.page.locator("#test-button")
    await expect(button).to_have_text("Click me")
    await expect(button).to_contain_class("ms-Button")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_blueprint(display: DisplayFixture):
    Button = component_from_npm("@blueprintjs/core", "Button", version="6")

    @reactpy.component
    def App():
        return Button({"intent": "primary", "id": "test-button"}, "Click me")

    await display.show(App)
    button = display.page.locator("#test-button")
    await expect(button).to_have_text("Click me")
    await expect(button).to_contain_class("bp6-button")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_grommet(display: DisplayFixture):
    Grommet, Button = component_from_npm("grommet", ["Grommet", "Button"], version="2")

    @reactpy.component
    def App():
        return Grommet(
            Button({"primary": True, "label": "Click me", "id": "test-button"})
        )

    await display.show(App)
    button = display.page.locator("#test-button")
    await expect(button).to_have_text("Click me")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_evergreen(display: DisplayFixture):
    Button = component_from_npm("evergreen-ui", "Button", version="7")

    @reactpy.component
    def App():
        return Button({"appearance": "primary", "id": "test-button"}, "Click me")

    await display.show(App)
    button = display.page.locator("#test-button")
    await expect(button).to_have_text("Click me")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_component_from_npm_react_spinners(display: DisplayFixture):
    ClipLoader = component_from_npm("react-spinners", "ClipLoader", version="0.17.0")

    @reactpy.component
    def App():
        return ClipLoader(
            {
                "color": "red",
                "loading": True,
                "size": 150,
                "data-testid": "loader",
            }
        )

    await display.show(App)
    # react-spinners renders a span with the loader
    # We can check if it exists. It might not have an ID we can easily set on the root if it doesn't forward props well,
    # but let's try wrapping it.
    loader = display.page.locator("span[data-testid='loader']")
    await expect(loader).to_be_visible()


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_nested_npm_components(display: DisplayFixture):
    ChakraProvider, Box, _ = _get_chakra_components()
    BootstrapButton = component_from_npm("react-bootstrap", "Button", version="2")

    @reactpy.component
    def App():
        return ChakraProvider(
            Box(
                {
                    "id": "chakra-box",
                    "p": 4,
                    "color": "white",
                    "bg": "blue.500",
                },
                BootstrapButton(
                    {"variant": "light", "id": "bootstrap-button"},
                    "Nested Button",
                ),
            )
        )

    await display.show(App)

    box = display.page.locator("#chakra-box")
    await expect(box).to_be_visible()

    button = display.page.locator("#bootstrap-button")
    await expect(button).to_have_text("Nested Button")
    await expect(button).to_contain_class("btn")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_interleaved_npm_and_server_components(display: DisplayFixture):
    Card = component_from_npm("antd", "Card", version="6")
    Button = component_from_npm("@mui/material", "Button", version="7")

    @reactpy.component
    def App():
        return Card(
            {"title": "Antd Card", "id": "antd-card"},
            html.div(
                {
                    "id": "server-div",
                    "style": {"padding": "10px", "border": "1px solid red"},
                },
                "Server Side Div",
                Button({"variant": "contained", "id": "mui-button"}, "MUI Button"),
            ),
        )

    await display.show(App)

    card = display.page.locator("#antd-card")
    await expect(card).to_be_visible()

    server_div = display.page.locator("#server-div")
    await expect(server_div).to_be_visible()
    await expect(server_div).to_contain_text("Server Side Div")

    button = display.page.locator("#mui-button")
    await expect(button).to_contain_text("MUI Button")  # MUI capitalizes
    await expect(button).to_have_css("text-transform", "uppercase")


@pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)
async def test_complex_nested_material_ui(display: DisplayFixture):
    mui_components = component_from_npm(
        "@mui/material",
        ["Button", "Card", "CardContent", "Typography", "Box", "Stack"],
        version="7",
    )
    Button, Card, CardContent, Typography, Box, Stack = mui_components

    @reactpy.component
    def App():
        return Box(
            {
                "sx": {
                    "padding": "20px",
                    "backgroundColor": "#f5f5f5",
                    "height": "100vh",
                }
            },
            Stack(
                {"spacing": 2, "direction": "column", "alignItems": "center"},
                Typography(
                    {"variant": "h4", "component": "h1", "gutterBottom": True},
                    "Complex Nested UI Test",
                ),
                Card(
                    {"sx": {"minWidth": 300, "maxWidth": 500}},
                    CardContent(
                        Typography(
                            {
                                "sx": {"fontSize": 14},
                                "color": "text.secondary",
                                "gutterBottom": True,
                            },
                            "Word of the Day",
                        ),
                        Typography(
                            {"variant": "h5", "component": "div"},
                            "be-nev-o-lent",
                        ),
                        Typography(
                            {"sx": {"mb": 1.5}, "color": "text.secondary"},
                            "adjective",
                        ),
                        Typography({"variant": "body2"}, "well meaning and kindly."),
                    ),
                    Box(
                        {
                            "sx": {
                                "padding": "10px",
                                "display": "flex",
                                "justifyContent": "flex-end",
                            }
                        },
                        Button(
                            {
                                "size": "small",
                                "variant": "contained",
                                "id": "learn-more-btn",
                            },
                            "Learn More",
                        ),
                    ),
                ),
            ),
        )

    await display.show(App)

    # Check if the button is visible and has correct text
    btn = display.page.locator("#learn-more-btn")
    await expect(btn).to_be_visible()
    # Material UI transforms text to uppercase by default
    await expect(btn).to_contain_text("Learn More")
    await expect(btn).to_have_css("text-transform", "uppercase")

    # Check if Card is rendered (it usually has MuiCard-root class)
    # We can't easily select by ID as we didn't put one on Card, but we can check structure if needed.
    # But let's just check if the text "be-nev-o-lent" is visible
    text = display.page.locator("text=be-nev-o-lent")
    await expect(text).to_be_visible()


def _get_chakra_components():
    # FIXME: Chakra UI requires `defaultSystem` to be passed in to the provider. We need
    # to figure out how to do this better in the long term, perhaps by enhancing
    # `component_from_npm` to support such cases.
    from reactpy.reactjs import component_from_string

    wrapper_js = """
    import { ChakraProvider as _ChakraProvider, defaultSystem, Box as _Box, Button as _Button } from "https://esm.sh/v135/@chakra-ui/react@3?external=react,react-dom,react/jsx-runtime&bundle&target=es2020";
    import * as React from "react";

    export function ChakraProvider(props) {
        return React.createElement(_ChakraProvider, { value: defaultSystem, ...props });
    }

    export const Box = _Box;
    export const Button = _Button;
    """
    return component_from_string(wrapper_js, ["ChakraProvider", "Box", "Button"])
