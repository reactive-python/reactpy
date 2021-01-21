import pytest

import idom
from idom.server.utils import find_builtin_server_type


def test_no_application_until_running():
    @idom.component
    def AnyComponent():
        pass

    server = find_builtin_server_type("PerClientStateServer")(AnyComponent)

    with pytest.raises(RuntimeError, match="No application"):
        server.application
