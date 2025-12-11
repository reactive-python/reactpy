import pytest

import reactpy
from reactpy import html
from reactpy.reactjs import component_from_npm, import_reactjs
from reactpy.testing import BackendFixture, DisplayFixture


@pytest.mark.anyio
async def test_component_from_npm_react_bootstrap():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            Button = component_from_npm("react-bootstrap", "Button", version="2.10.2")

            @reactpy.component
            def App():
                return Button({"variant": "primary", "id": "test-button"}, "Click me")

            await display.show(App)

            button = await display.page.wait_for_selector("#test-button")
            assert await button.inner_text() == "Click me"

            # Check if it has the correct class for primary variant
            # React Bootstrap buttons usually have 'btn' and 'btn-primary' classes
            classes = await button.get_attribute("class")
            assert "btn" in classes
            assert "btn-primary" in classes


@pytest.mark.anyio
async def test_component_from_npm_material_ui():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            Button = component_from_npm("@mui/material", "Button")

            @reactpy.component
            def App():
                return Button({"variant": "contained", "id": "test-button"}, "Click me")

            await display.show(App)
            button = await display.page.wait_for_selector("#test-button")
            # Material UI transforms text to uppercase by default
            assert await button.inner_text() == "CLICK ME"
            classes = await button.get_attribute("class")
            assert "MuiButton-root" in classes


@pytest.mark.anyio
async def test_component_from_npm_antd():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            # Try antd v4 which might be more stable with esm.sh
            Button = component_from_npm("antd", "Button", version="4.24.15")

            @reactpy.component
            def App():
                return Button({"type": "primary", "id": "test-button"}, "Click me")

            await display.show(App)
            button = await display.page.wait_for_selector("#test-button")
            assert "Click me" in await button.inner_text()
            classes = await button.get_attribute("class")
            assert "ant-btn" in classes


@pytest.mark.anyio
async def test_component_from_npm_chakra_ui():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            ChakraProvider, Button = component_from_npm(
                "@chakra-ui/react", ["ChakraProvider", "Button"], version="2.8.2"
            )

            @reactpy.component
            def App():
                return ChakraProvider(
                    Button({"colorScheme": "blue", "id": "test-button"}, "Click me")
                )

            await display.show(App)
            button = await display.page.wait_for_selector("#test-button")
            assert await button.inner_text() == "Click me"
            classes = await button.get_attribute("class")
            assert "chakra-button" in classes


@pytest.mark.anyio
async def test_component_from_npm_semantic_ui_react():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            Button = component_from_npm("semantic-ui-react", "Button")

            @reactpy.component
            def App():
                return Button({"primary": True, "id": "test-button"}, "Click me")

            await display.show(App)
            button = await display.page.wait_for_selector("#test-button")
            assert await button.inner_text() == "Click me"
            classes = await button.get_attribute("class")
            assert "ui" in classes
            assert "button" in classes


@pytest.mark.anyio
async def test_component_from_npm_mantine():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            MantineProvider, Button = component_from_npm(
                "@mantine/core", ["MantineProvider", "Button"], version="7.3.0"
            )

            @reactpy.component
            def App():
                return MantineProvider(Button({"id": "test-button"}, "Click me"))

            await display.show(App)
            button = await display.page.wait_for_selector("#test-button")
            assert await button.inner_text() == "Click me"
            classes = await button.get_attribute("class")
            assert "mantine-Button-root" in classes


@pytest.mark.anyio
async def test_component_from_npm_fluent_ui():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            PrimaryButton = component_from_npm("@fluentui/react", "PrimaryButton")

            @reactpy.component
            def App():
                return PrimaryButton({"id": "test-button"}, "Click me")

            await display.show(App)
            button = await display.page.wait_for_selector("#test-button")
            assert await button.inner_text() == "Click me"
            classes = await button.get_attribute("class")
            assert "ms-Button" in classes


@pytest.mark.anyio
async def test_component_from_npm_blueprint():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            Button = component_from_npm("@blueprintjs/core", "Button")

            @reactpy.component
            def App():
                return Button({"intent": "primary", "id": "test-button"}, "Click me")

            await display.show(App)
            button = await display.page.wait_for_selector("#test-button")
            assert await button.inner_text() == "Click me"
            classes = await button.get_attribute("class")
            assert any(c.startswith("bp") and "button" in c for c in classes.split())


@pytest.mark.anyio
async def test_component_from_npm_grommet():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            Grommet, Button = component_from_npm("grommet", ["Grommet", "Button"])

            @reactpy.component
            def App():
                return Grommet(
                    Button({"primary": True, "label": "Click me", "id": "test-button"})
                )

            await display.show(App)
            button = await display.page.wait_for_selector("#test-button")
            assert await button.inner_text() == "Click me"


@pytest.mark.anyio
async def test_component_from_npm_evergreen():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            Button = component_from_npm("evergreen-ui", "Button")

            @reactpy.component
            def App():
                return Button(
                    {"appearance": "primary", "id": "test-button"}, "Click me"
                )

            await display.show(App)
            button = await display.page.wait_for_selector("#test-button")
            assert await button.inner_text() == "Click me"


@pytest.mark.anyio
async def test_component_from_npm_react_spinners():
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend) as display:
            ClipLoader = component_from_npm("react-spinners", "ClipLoader")

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
            loader = await display.page.wait_for_selector("span[data-testid='loader']")
            assert await loader.is_visible()
