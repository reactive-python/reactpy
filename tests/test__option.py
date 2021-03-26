import os
from unittest import mock

import pytest

from idom._option import Option


def test_option_repr():
    opt = Option("A_FAKE_OPTION", "some-value")
    assert opt.name == "A_FAKE_OPTION"
    assert repr(opt) == "Option(A_FAKE_OPTION='some-value')"


@mock.patch.dict(os.environ, {"A_FAKE_OPTION": "value-from-environ"})
def test_option_from_os_environ():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert opt.get() == "value-from-environ"


def test_option_from_default():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert opt.get() == "default-value"
    assert opt.get() is opt.default


@mock.patch.dict(os.environ, {"A_FAKE_OPTION": "1"})
def test_option_validator():
    opt = Option("A_FAKE_OPTION", False, validator=lambda x: bool(int(x)))

    assert opt.get() is True

    opt.set("0")
    assert opt.get() is False

    with pytest.raises(ValueError, match="invalid literal for int"):
        opt.set("not-an-int")


def test_immutable_option():
    opt = Option("A_FAKE_OPTION", "default-value", mutable=False)
    assert not opt.mutable
    with pytest.raises(TypeError, match="cannot be modified after initial load"):
        opt.set("a-new-value")
    with pytest.raises(TypeError, match="cannot be modified after initial load"):
        opt.reset()


def test_option_reset():
    opt = Option("A_FAKE_OPTION", "default-value")
    opt.set("a-new-value")
    opt.reset()
    assert opt.get() is opt.default
    assert not opt.is_set()


@mock.patch.dict(os.environ, {"A_FAKE_OPTION": "value-from-environ"})
def test_option_reload():
    opt = Option("A_FAKE_OPTION", "default-value")
    opt.set("some-other-value")
    opt.reload()
    assert opt.get() == "value-from-environ"


def test_option_set():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert not opt.is_set()
    opt.set("a-new-value")
    assert opt.is_set()


def test_option_set_default():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert not opt.is_set()
    assert opt.set_default("new-value") == "new-value"
    assert opt.is_set()
