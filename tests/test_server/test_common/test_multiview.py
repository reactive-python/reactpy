import pytest

import idom
from idom.server import all_implementations
from idom.server import fastapi as idom_fastapi
from idom.server import flask as idom_flask
from idom.server import sanic as idom_sanic
from idom.server import starlette as idom_starlette
from idom.testing import ServerMountPoint
from tests.driver_utils import no_such_element


@pytest.fixture(
    params=list(all_implementations()),
    ids=lambda cls: f"{cls.__module__}.{cls.__name__}",
)
async def server_mount_point(request):
    async with ServerMountPoint(request.param) as mount_point:
        yield mount_point


def test_multiview_server(driver_get, driver, server_mount_point):
    manual_id = server_mount_point.mount.add(
        "manually_set_id",
        lambda: idom.html.h1({"id": "e1"}, ["e1"]),
    )
    auto_view_id = server_mount_point.mount.add(
        None,
        lambda: idom.html.h1({"id": "e2"}, ["e2"]),
    )

    driver_get({"view_id": manual_id})
    driver.find_element("id", "e1")

    driver_get({"view_id": auto_view_id})
    driver.find_element("id", "e2")

    server_mount_point.mount.remove(auto_view_id)
    server_mount_point.mount.remove(manual_id)

    driver.refresh()

    assert no_such_element(driver, "id", "e1")
    assert no_such_element(driver, "id", "e2")

    server_mount_point.log_records.clear()
