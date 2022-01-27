from idom import component, html, use_state
from idom.utils import Ref


def use_toggle():
    state, set_state = use_state(True)
    return state, lambda: set_state(not state)


def use_counter():
    state, set_state = use_state(1)
    return state, lambda: set_state(state + 1)


def test_script_mount_unmount(driver, driver_wait, display):
    toggle_is_mounted = Ref()

    @component
    def Root():
        is_mounted, toggle_is_mounted.current = use_toggle()
        if is_mounted:
            el = HasScript()
        else:
            el = html.div()

        return html.div(
            html.div({"id": "mount-state", "data-value": False}),
            el,
        )

    @component
    def HasScript():
        return html.script(
            """() => {
                const mapping = {"false": false, "true": true};
                const mountStateEl = document.getElementById("mount-state");
                mountStateEl.setAttribute(
                    "data-value", !mapping[mountStateEl.getAttribute("data-value")]);
                return () => mountStateEl.setAttribute(
                    "data-value", !mapping[mountStateEl.getAttribute("data-value")]);
            }"""
        )

    display(Root)

    mount_state = driver.find_element("id", "mount-state")

    driver_wait.until(lambda d: mount_state.get_attribute("data-value") == "true")

    toggle_is_mounted.current()

    driver_wait.until(lambda d: mount_state.get_attribute("data-value") == "false")

    toggle_is_mounted.current()

    driver_wait.until(lambda d: mount_state.get_attribute("data-value") == "true")


def test_script_re_run_on_content_change(driver, driver_wait, display):
    incr_count = Ref()

    @component
    def HasScript():
        count, incr_count.current = use_counter()
        return html.div(
            html.div({"id": "mount-count", "data-value": 0}),
            html.div({"id": "unmount-count", "data-value": 0}),
            html.script(
                f"""() => {{
                    const mountCountEl = document.getElementById("mount-count");
                    const unmountCountEl = document.getElementById("unmount-count");
                    mountCountEl.setAttribute("data-value", {count});
                    return () => unmountCountEl.setAttribute("data-value", {count});;
                }}"""
            ),
        )

    display(HasScript)

    mount_count = driver.find_element("id", "mount-count")
    unmount_count = driver.find_element("id", "unmount-count")

    driver_wait.until(lambda d: mount_count.get_attribute("data-value") == "1")
    driver_wait.until(lambda d: unmount_count.get_attribute("data-value") == "0")

    incr_count.current()

    driver_wait.until(lambda d: mount_count.get_attribute("data-value") == "2")
    driver_wait.until(lambda d: unmount_count.get_attribute("data-value") == "1")

    incr_count.current()

    driver_wait.until(lambda d: mount_count.get_attribute("data-value") == "3")
    driver_wait.until(lambda d: unmount_count.get_attribute("data-value") == "2")
