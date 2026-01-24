from pathlib import Path

import pytest

import reactpy
from reactpy import html
from reactpy.reactjs import component_from_string, import_reactjs
from reactpy.testing import BackendFixture, DisplayFixture

JS_FIXTURES_DIR = Path(__file__).parent / "js_fixtures"


@pytest.fixture(scope="module")
async def display(browser):
    """Override for the display fixture that includes ReactJS."""
    async with BackendFixture(html_head=html.head(import_reactjs())) as backend:
        async with DisplayFixture(backend=backend, browser=browser) as new_display:
            yield new_display


async def test_nested_client_side_components(display: DisplayFixture):
    # Module A
    ComponentA = component_from_string(
        """
        import React from "react";
        export function ComponentA({ children }) {
            return React.createElement("div", { id: "component-a" }, children);
        }
        """,
        "ComponentA",
        name="module-a",
    )

    # Module B
    ComponentB = component_from_string(
        """
        import React from "react";
        export function ComponentB({ children }) {
            return React.createElement("div", { id: "component-b" }, children);
        }
        """,
        "ComponentB",
        name="module-b",
    )

    @reactpy.component
    def App():
        return ComponentA(
            ComponentB(reactpy.html.div({"id": "server-side"}, "Server Side Content"))
        )

    await display.show(App)

    # Check that all components are rendered
    await display.page.wait_for_selector("#component-a")
    await display.page.wait_for_selector("#component-b")
    await display.page.wait_for_selector("#server-side")


async def test_interleaved_client_server_components(display: DisplayFixture):
    # Module C
    ComponentC = component_from_string(
        """
        import React from "react";
        export function ComponentC({ children }) {
            return React.createElement("div", { id: "component-c", className: "component-c" }, children);
        }
        """,
        "ComponentC",
        name="module-c",
    )

    @reactpy.component
    def App():
        return reactpy.html.div(
            {"id": "root-server"},
            ComponentC(
                reactpy.html.div(
                    {"id": "nested-server"},
                    ComponentC(
                        reactpy.html.span({"id": "deep-server"}, "Deep Content")
                    ),
                )
            ),
        )

    await display.show(App)

    await display.page.wait_for_selector("#root-server")
    await display.page.wait_for_selector(".component-c")
    await display.page.wait_for_selector("#nested-server")
    # We need to check that there are two component-c elements
    elements = await display.page.query_selector_all(".component-c")
    assert len(elements) == 2
    await display.page.wait_for_selector("#deep-server")


async def test_nest_custom_component_under_web_component(display: DisplayFixture):
    """
    Fix https://github.com/reactive-python/reactpy/discussions/1323

    Custom components (i.e those wrapped in the component decorator) were not able to
    be nested under web components.
    """
    Container = reactpy.reactjs.component_from_file(
        JS_FIXTURES_DIR / "nest-custom-under-web.js", "Container", name="nest-custom-under-web"
    )

    @reactpy.component
    def CustomComponent():
        return reactpy.html.div(reactpy.html.h1({"id": "my-header"}, "Header 1"))

    await display.show(lambda: Container(CustomComponent()))

    element = await display.page.wait_for_selector("#my-header", state="attached")
    assert await element.inner_text() == "Header 1"
