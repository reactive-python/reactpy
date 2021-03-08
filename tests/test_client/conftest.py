import pytest

import idom


@pytest.fixture
def htm():
    return idom.install("htm@3.0.4")


@pytest.fixture
def victory():
    return idom.install("victory@35.4.0")
