from pathlib import Path

import idom


HERE = Path(__file__).parent


def test_shared_hostwap(driver, display):
    """Ensure shared hotswapping works

    This basically means that previously rendered views of a hotswap element get updated
    when a new view is mounted, not just the next time it is re-displayed

    In this test we construct a scenario where clicking a button will cause a pre-existing
    hotswap element to be updated
    """

    @idom.element
    def ButtonSwapsDivs():
        count = idom.Ref(0)

        @idom.event
        async def on_click(event):
            count.current += 1
            mount(idom.html.div, {"id": f"hotswap-{count.current}"}, count.current)

        incr = idom.html.button({"onClick": on_click, "id": "incr-button"}, "incr")

        mount, make_hostswap = idom.widgets.hotswap(shared=True)
        mount(idom.html.div, {"id": f"hotswap-{count.current}"}, count.current)
        hotswap_view = make_hostswap()

        return idom.html.div(incr, hotswap_view)

    display(ButtonSwapsDivs)

    client_incr_button = driver.find_element_by_id("incr-button")

    driver.find_element_by_id("hotswap-0")
    client_incr_button.click()
    driver.find_element_by_id("hotswap-1")
    client_incr_button.click()
    driver.find_element_by_id("hotswap-2")
