from pathlib import Path

import idom
from idom.testing import ServerMountPoint


JS_DIR = Path(__file__).parent / "js"


def test_automatic_reconnect(create_driver):
    # we need to wait longer here because the automatic reconnect is not instance
    driver = create_driver(implicit_wait_timeout=10, page_load_timeout=10)

    @idom.component
    def OldComponent():
        return idom.html.p({"id": "old-component"}, "old")

    mount_point = ServerMountPoint()

    with mount_point:
        mount_point.mount(OldComponent)
        driver.get(mount_point.url())
        # ensure the element is displayed before stopping the server
        driver.find_element_by_id("old-component")

    # the server is disconnected but the last view state is still shown
    driver.find_element_by_id("old-component")

    set_state = idom.Ref(None)

    @idom.component
    def NewComponent():
        state, set_state.current = idom.hooks.use_state(0)
        return idom.html.p({"id": f"new-component-{state}"}, f"new-{state}")

    with mount_point:
        mount_point.mount(NewComponent)

        # Note the lack of a page refresh before looking up this new component. The
        # client should attempt to reconnect and display the new view automatically.
        driver.find_element_by_id("new-component-0")

        # check that we can resume normal operation
        set_state.current(1)
        driver.find_element_by_id("new-component-1")


def test_that_js_module_unmount_is_called(driver, driver_wait, display):
    module = idom.Module(
        "set-flag-when-unmount-is-called",
        source_file=JS_DIR / "set-flag-when-unmount-is-called.js",
    )

    set_current_component = idom.Ref(None)

    @idom.component
    def ShowCurrentComponent():
        current_component, set_current_component.current = idom.hooks.use_state(
            lambda: module.SomeComponent(
                {"id": "some-component", "text": "initial component"}
            )
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
