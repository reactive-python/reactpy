import pytest

import idom
from idom.server.utils import find_builtin_server_type


def test_no_application_until_running():
    @idom.element
    def AnyElement():
        pass

    server = find_builtin_server_type("PerClientStateServer")(AnyElement)

    with pytest.raises(RuntimeError, match="No application"):
        server.application
