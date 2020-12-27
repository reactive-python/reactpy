import asyncio

import pytest
from sanic import Sanic

import idom
from idom.server.sanic import PerClientStateServer
from idom.testing import create_multiview_mount_and_server


@pytest.fixture(scope="module")
def mount_and_server(host, port):
    return create_multiview_mount_and_server(
        PerClientStateServer,
        host,
        port,
        # test that we can use a custom app instance
        app=Sanic(),
    )


def test_serve_has_loop_attribute(server):
    assert isinstance(server.loop, asyncio.AbstractEventLoop)


def test_no_application_until_running():
    @idom.element
    def AnyElement():
        pass

    server = idom.server.sanic.PerClientStateServer(AnyElement)

    with pytest.raises(RuntimeError, match="No application"):
        server.application
