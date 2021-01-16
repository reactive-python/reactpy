import pytest

import idom
from idom.server.default import PerClientStateServer


def test_no_application_until_running():
    @idom.element
    def AnyElement():
        pass

    server = PerClientStateServer(AnyElement)

    with pytest.raises(RuntimeError, match="No application"):
        server.application
