import pytest

import idom
from idom.server.utils import all_implementations
from idom.testing import ServerFixture


@pytest.fixture(
    params=list(all_implementations()),
    ids=lambda imp: imp.__name__,
)
def server_mount_point(request):
    with ServerFixture(request.param) as mount_point:
        yield mount_point


def test_display_simple_hello_world(driver, display):
    @idom.component
    def Hello():
        return idom.html.p({"id": "hello"}, ["Hello World"])

    display(Hello)

    assert driver.find_element("id", "hello")

    # test that we can reconnect succefully
    driver.refresh()

    assert driver.find_element("id", "hello")


def test_display_simple_click_counter(driver, driver_wait, display):
    def increment(count):
        return count + 1

    @idom.component
    def Counter():
        count, set_count = idom.hooks.use_state(0)
        return idom.html.button(
            {
                "id": "counter",
                "onClick": lambda event: set_count(increment),
            },
            f"Count: {count}",
        )

    display(Counter)

    client_counter = driver.find_element("id", "counter")

    for i in range(3):
        driver_wait.until(
            lambda driver: client_counter.get_attribute("innerHTML") == f"Count: {i}"
        )
        client_counter.click()


def test_module_from_template(driver, display):
    victory = idom.web.module_from_template("react", "victory-bar@35.4.0")
    VictoryBar = idom.web.export(victory, "VictoryBar")
    display(VictoryBar)
    driver.find_element_by_class_name("VictoryContainer")
