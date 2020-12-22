import pytest

import idom


@pytest.fixture
def victory():
    return idom.install("victory@35.4.0")
