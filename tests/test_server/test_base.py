import pytest

import idom
from idom.server.utils import find_builtin_server_type


@idom.component
def AnyComponent():
    pass


def test_no_application_until_running():
    server = find_builtin_server_type("PerClientStateServer")(AnyComponent)
    with pytest.raises(RuntimeError, match="No application"):
        server.app
