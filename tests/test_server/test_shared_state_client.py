import pytest

import idom
from idom.server import hotswap_server
from idom.server.sanic import SharedClientStateServer


@pytest.fixture(scope="module")
def server_type():
    return SharedClientStateServer


@pytest.fixture(scope="module")
def mount_and_server(
    application, fixturized_server_type, host, port, last_server_error,
):
    """An IDOM layout mount function and server as a tuple

    The ``mount`` and ``server`` fixtures use this.
    """

    mount, server = hotswap_server(
        fixturized_server_type,
        host,
        port,
        server_options={"cors": True, "last_server_error": last_server_error},
        run_options={},
        sync_views=True,
        app=application,
    )
    return mount, server


def test_shared_client_state(create_driver, mount, server_url):
    driver_1 = create_driver()
    driver_2 = create_driver()

    @idom.element
    async def IncrCounter(self, count=0):
        @idom.event
        async def incr_on_click(event):
            self.update(count + 1)

        button = idom.html.button(
            {"onClick": incr_on_click, "id": "incr-button"}, "click to increment"
        )

        return idom.html.div(button, idom.html.div({"id": f"count-is-{count}"}, count))

    mount(IncrCounter)

    driver_1.get(server_url)
    driver_2.get(server_url)

    client_1_button = driver_1.find_element_by_id("incr-button")
    client_2_button = driver_2.find_element_by_id("incr-button")

    driver_1.find_element_by_id("count-is-0")
    driver_2.find_element_by_id("count-is-0")

    client_1_button.click()

    driver_1.find_element_by_id("count-is-1")
    driver_2.find_element_by_id("count-is-1")

    client_2_button.click()

    driver_1.find_element_by_id("count-is-2")
    driver_2.find_element_by_id("count-is-2")
