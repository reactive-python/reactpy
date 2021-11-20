import pytest

import idom
from idom.server import fastapi as idom_fastapi
from idom.server import flask as idom_flask
from idom.server import sanic as idom_sanic
from idom.server import tornado as idom_tornado
from idom.server.prefab import multiview_server
from idom.testing import ServerMountPoint
from tests.driver_utils import no_such_element


@pytest.fixture(
    params=[
        # add new PerClientStateServer implementations here to
        # run a suite of tests which check basic functionality
        idom_sanic.PerClientStateServer,
        idom_flask.PerClientStateServer,
        idom_tornado.PerClientStateServer,
        idom_fastapi.PerClientStateServer,
    ],
    ids=lambda cls: f"{cls.__module__}.{cls.__name__}",
)
def server_mount_point(request):
    with ServerMountPoint(
        request.param,
        mount_and_server_constructor=multiview_server,
    ) as mount_point:
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
    driver.find_element_by_id("e1")

    driver_get({"view_id": auto_view_id})
    driver.find_element_by_id("e2")

    server_mount_point.mount.remove(auto_view_id)
    server_mount_point.mount.remove(manual_id)

    driver.refresh()

    assert no_such_element(driver, "id", "e1")
    assert no_such_element(driver, "id", "e2")

    server_mount_point.log_records.clear()
