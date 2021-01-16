import pytest
from sanic import Sanic

import idom
from idom.server.sanic import PerClientStateServer
from idom.testing import ServerMountPoint


@pytest.fixture(scope="module")
def server_mount_point():
    return ServerMountPoint(
        PerClientStateServer,
        # test that we can use a custom app instance
        app=Sanic(),
    )


def test_no_application_until_running():
    @idom.element
    def AnyElement():
        pass

    server = idom.server.sanic.PerClientStateServer(AnyElement)

    with pytest.raises(RuntimeError, match="No application"):
        server.application
