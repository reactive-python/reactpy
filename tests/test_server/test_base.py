import pytest
import sanic

import idom
from idom.server.sanic import PerClientStateServer
from idom.server.utils import find_builtin_server_type


@idom.component
def AnyComponent():
    pass


def test_no_application_until_running():
    server = find_builtin_server_type("PerClientStateServer")(AnyComponent)
    with pytest.raises(RuntimeError, match="No application"):
        server.application


def test_cannot_register_app_twice():
    server = PerClientStateServer(AnyComponent)
    server.register(sanic.Sanic())
    with pytest.raises(RuntimeError, match="Already registered"):
        server.register(sanic.Sanic())
