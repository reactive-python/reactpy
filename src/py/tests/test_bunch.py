import pytest

from idom.bunch import StaticBunch, DynamicBunch


def test_static_bunch_is_static():
    b = StaticBunch()

    with pytest.raises(TypeError):
        b.a = 1

    with pytest.raises(TypeError):
        b["a"] = 1

    with pytest.raises(TypeError):
        del b.a

    with pytest.raises(TypeError):
        del b["a"]


def test_test_static_bunch_is_dict_like():
    # init via keyword
    b_1 = StaticBunch(a=1)

    assert b_1.a == 1
    assert b_1["a"] == 1
    assert "a" in b_1
    assert hasattr(b_1, "a")

    # init via dict
    b_2 = StaticBunch({"a": 1})

    assert b_2.a == 1
    assert b_2["a"] == 1
    assert "a" in b_1
    assert hasattr(b_1, "a")


def test_dynamic_bunch_is_dynamic():
    b = DynamicBunch()

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
