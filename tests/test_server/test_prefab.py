import pytest

import idom
from idom.server.default import PerClientStateServer
from idom.server.prefab import multiview_server
from idom.testing import ServerMountPoint

from tests.driver_utils import no_such_element


@pytest.fixture
def server_mount_point():
    return ServerMountPoint(
        PerClientStateServer, mount_and_server_constructor=multiview_server
    )


def test_multiview_server(driver_get, driver, mount):
    manual_id = mount["manually_set_id"](lambda: idom.html.h1({"id": "e1"}, ["e1"]))
    auto_view_id = mount(lambda: idom.html.h1({"id": "e2"}, ["e2"]))

    driver_get({"view_id": manual_id})
    driver.find_element_by_id("e1")

    driver_get({"view_id": auto_view_id})
    driver.find_element_by_id("e2")

    mount.remove(auto_view_id)
    mount.remove(manual_id)

    driver.refresh()

    assert no_such_element(driver, "id", "e1")
    assert no_such_element(driver, "id", "e2")
