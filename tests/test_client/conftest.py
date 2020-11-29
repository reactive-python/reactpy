import pytest

import idom


@pytest.fixture
def victory_js(install):
    install("victory@35.4.0")
    return idom.Module("victory")
