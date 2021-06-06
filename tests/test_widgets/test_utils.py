from pathlib import Path

import idom


HERE = Path(__file__).parent


def test_multiview_repr():
    assert str(idom.widgets.utils.MultiViewMount({})) == "MultiViewMount({})"


def test_hostwap_update_on_change(driver, display):
    """Ensure shared hotswapping works

    This basically means that previously rendered views of a hotswap component get updated
    when a new view is mounted, not just the next time it is re-displayed

    In this test we construct a scenario where clicking a button will cause a pre-existing
    hotswap component to be updated
    """

    def make_next_count_constructor(count):
        """We need to construct a new function so they're different when we set_state"""

        def constructor():
            count.current += 1
            return idom.html.div({"id": f"hotswap-{count.current}"}, count.current)

        return constructor

    @idom.component
    def ButtonSwapsDivs():
        count = idom.Ref(0)

        @idom.event
        async def on_click(event):
            mount(make_next_count_constructor(count))

        incr = idom.html.button({"onClick": on_click, "id": "incr-button"}, "incr")

        mount, make_hostswap = idom.widgets.hotswap(update_on_change=True)
        mount(make_next_count_constructor(count))
        hotswap_view = make_hostswap()

        return idom.html.div(incr, hotswap_view)

    display(ButtonSwapsDivs)

    client_incr_button = driver.find_element_by_id("incr-button")

    driver.find_element_by_id("hotswap-1")
    client_incr_button.click()
    driver.find_element_by_id("hotswap-2")
    client_incr_button.click()
    driver.find_element_by_id("hotswap-3")
