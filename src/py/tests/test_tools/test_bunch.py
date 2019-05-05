import pytest

from idom.tools.bunch import Bunch


def test_bunch_is_dynamic():
    b = Bunch()

    # attribute assignment
    b.a = 1

    assert b.a == 1
    assert b["a"] == 1
    assert "a" in b
    assert hasattr(b, "a")

    del b.a
    assert not hasattr(b, "a")
    assert "a" not in b
    with pytest.raises(KeyError):
        b["a"]

    # item assignment
    b["a"] = 1

    assert b.a == 1
    assert b["a"] == 1
    assert "a" in b
    assert hasattr(b, "a")

    del b.a
    assert not hasattr(b, "a")
    assert "a" not in b
    with pytest.raises(KeyError):
        b["a"]
