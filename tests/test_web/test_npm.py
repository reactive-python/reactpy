import pytest

import reactpy
from reactpy import html
from reactpy.testing import BackendFixture, DisplayFixture
from reactpy.web import reactjs_component_from_npm, reactjs_import_map


@pytest.mark.anyio
async def test_reactjs_component_from_npm_react_bootstrap():
    async with BackendFixture(html_head=html.head(reactjs_import_map())) as backend:
        async with DisplayFixture(backend=backend) as display:
            Button = reactjs_component_from_npm(
                "react-bootstrap", "Button", version="2.10.2"
            )

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
