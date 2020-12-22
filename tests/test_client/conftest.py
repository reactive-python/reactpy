import pytest

import idom


@pytest.fixture
def victory_js(install):
    return idom.install("victory@35.4.0")
