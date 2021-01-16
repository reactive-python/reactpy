import pytest

import idom
from idom.server.flask import PerClientStateServer
from idom.testing import ServerMountPoint


@pytest.fixture(scope="module")
def server_mount_point():
    """An IDOM layout mount function and server as a tuple

    The ``mount`` and ``server`` fixtures use this.
    """
    return ServerMountPoint(PerClientStateServer, server_config={"cors": True})


def test_display_simple_hello_world(driver, display):
    @idom.element
    def Hello():
        return idom.html.p({"id": "hello"}, ["Hello World"])

    display(Hello)

    assert driver.find_element_by_id("hello")


def test_display_simple_click_counter(driver, display):
    def increment(count):
        return count + 1

    @idom.element
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

    client_counter = driver.find_element_by_id("counter")

    for i in range(3):
        assert client_counter.get_attribute("innerHTML") == f"Count: {i}"
        client_counter.click()


def test_installed_module(driver, display):
    victory = idom.install("victory@35.4.0")
    display(victory.VictoryBar)
    driver.find_element_by_class_name("VictoryContainer")
