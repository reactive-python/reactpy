from pathlib import Path

import idom
from idom.client.module import Module
from idom.testing import ServerMountPoint


HERE = Path(__file__).parent


def test_automatic_reconnect(create_driver):
    # we need to wait longer here because the automatic reconnect is not instance
    driver = create_driver(implicit_wait_timeout=10)

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


def test_vanilla_js_component_with_mount(driver, driver_wait, display):
    vanilla_js_component = Module(
        "vanilla-js-component",
        source_file=HERE / "js" / "vanilla-js-component.js",
        exports_mount=True,
    )

    set_text = idom.Ref(None)

    @idom.component
    def MakeVanillaHtml():
        text, set_text.current = idom.hooks.use_state("initial-text")
        return vanilla_js_component.ShowText({"text": text, "id": "my-el"})

    display(MakeVanillaHtml)

    parent_element = (
        # the reference to the child element changes on each render and become stale
        driver.find_element_by_id("my-el")
        # the reference to the parent element will stay the same
        .find_element_by_xpath("..")
    )

    driver_wait.until(
        lambda d: (
            (
                driver.find_element_by_id("my-el").get_attribute("innerText")
                == "initial-text"
            )
            and parent_element.get_attribute("mountCount") == "1"
            and parent_element.get_attribute("unmountCount") is None
        )
    )

    for i in range(1, 4):
        new_text = f"text-{i}"
        set_text.current(new_text)
        driver_wait.until(
            lambda d: (
                (
                    driver.find_element_by_id("my-el").get_attribute("innerText")
                    == new_text
                )
                and parent_element.get_attribute("mountCount") == str(i + 1)
                and parent_element.get_attribute("unmountCount") == str(i)
            )
        )
