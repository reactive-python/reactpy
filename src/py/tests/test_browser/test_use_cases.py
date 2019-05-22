import idom
from threading import Event
from selenium.webdriver.common.action_chains import ActionChains


def test_drag_and_drop(driver, display):
    drop_occured = Event()

    @idom.element
    async def Wrapper(self):
        return idom.html.div(Source(), Target())

    @idom.element
    async def Source(self):
        return idom.html.div(
            draggable=True,
            style={"backgroundColor": "red", "height": "30px", "width": "30px"},
            id="source",
        )

    @idom.element
    async def Target(self):
        events = idom.Events()

        @events.on(
            "DragOver", options={"preventDefault": True, "stopPropogation": True}
        )
        async def drag_over():
            pass

        @events.on("Drop")
        async def dropped():
            drop_occured.set()

        return idom.html.div(
            draggable=True,
            style={"backgroundColor": "blue", "height": "30px", "width": "30px"},
            eventHandlers=events,
            id="target",
        )

    display(Wrapper)

    dragged_item = driver.find_element_by_id("source")
    drag_destination = driver.find_element_by_id("target")
    ActionChains(driver).drag_and_drop(dragged_item, drag_destination).perform()

    assert drop_occured.wait(2)
