import pytest

import idom
from idom.server.utils import find_builtin_server_type
from idom.server.prefab import multiview_server
from idom.testing import ServerMountPoint

from tests.driver_utils import no_such_element


@pytest.fixture
def server_mount_point():
    return ServerMountPoint(
        find_builtin_server_type("PerClientStateServer"),
        mount_and_server_constructor=multiview_server,
    )


def test_multiview_server(driver_get, driver, server_mount_point):
    manual_id = server_mount_point.mount["manually_set_id"](
        lambda: idom.html.h1({"id": "e1"}, ["e1"])
    )
    auto_view_id = server_mount_point.mount(lambda: idom.html.h1({"id": "e2"}, ["e2"]))

    driver_get({"view_id": manual_id})
    driver.find_element_by_id("e1")

    driver_get({"view_id": auto_view_id})
    driver.find_element_by_id("e2")

    server_mount_point.mount.remove(auto_view_id)
    server_mount_point.mount.remove(manual_id)

    driver.refresh()

    assert no_such_element(driver, "id", "e1")
    assert no_such_element(driver, "id", "e2")
