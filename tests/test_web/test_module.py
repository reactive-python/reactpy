from pathlib import Path

import idom


JS_FIXTURES_DIR = Path(__file__).parent / "js_fixtures"


def test_that_js_module_unmount_is_called(driver, driver_wait, display):
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

    driver.find_element_by_id("some-component")

    set_current_component.current(
        idom.html.h1({"id": "some-other-component"}, "some other component")
    )

    # the new component has been displayed
    driver.find_element_by_id("some-other-component")

    # the unmount callback for the old component was called
    driver.find_element_by_id("unmount-flag")
