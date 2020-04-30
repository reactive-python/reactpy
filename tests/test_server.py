import pytest

import idom
from idom.server import multiview_server


@pytest.fixture(scope="module")
def mount_and_server(server_type, host, port):
    return multiview_server(server_type, host, port, run_options={"debug": True})


def test_multiview_server(driver_get, driver, mount, server):
    view_id_1 = mount(lambda: idom.html.h1({"id": "element1"}, ["e1"]))
    view_id_2 = mount(lambda: idom.html.h1({"id": "element2"}, ["e2"]))

    driver_get(f"view_id={view_id_1}")
    driver.find_element_by_id("element1")

    driver_get(f"view_id={view_id_2}")
    driver.find_element_by_id("element2")
