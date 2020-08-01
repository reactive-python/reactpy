import pytest

import idom
from idom.server import multiview_server

from tests.driver_utils import no_such_element


@pytest.fixture(scope="module")
def mount_and_server(
    fixturized_server_type, host, port, last_server_error, application
):
    return multiview_server(
        fixturized_server_type,
        host,
        port,
        server_options={"last_server_error": last_server_error},
        run_options={"debug": True},
        app=application,
    )


def test_multiview_server(driver_get, driver, mount, server):
    manual_id = mount["manually_set_id"](lambda: idom.html.h1({"id": "e1"}, ["e1"]))
    auto_view_id = mount(lambda: idom.html.h1({"id": "e2"}, ["e2"]))

    driver_get(f"view_id={manual_id}")
    driver.find_element_by_id("e1")

    driver_get(f"view_id={auto_view_id}")
    driver.find_element_by_id("e2")

    mount.remove(auto_view_id)
    mount.remove(manual_id)

    driver.refresh()

    assert no_such_element(driver, "id", "e1")
    assert no_such_element(driver, "id", "e2")
