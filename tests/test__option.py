import os
from unittest import mock

import pytest

from idom._option import Option


def test_option_repr():
    opt = Option("A_FAKE_OPTION", "some-value")
    assert repr(opt) == "Option(name='A_FAKE_OPTION', value='some-value')"


@mock.patch.dict(os.environ, {"A_FAKE_OPTION": "value-from-environ"})
def test_option_from_os_environ():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert opt.get() == "value-from-environ"


def test_option_from_default():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert opt.get() == "default-value"


@mock.patch.dict(os.environ, {"A_FAKE_OPTION": "1"})
def test_option_validator():
    opt = Option("A_FAKE_OPTION", False, validator=lambda x: bool(int(x)))

    assert opt.get() is True

    opt.set("0")
    assert opt.get() is False

    with pytest.raises(ValueError, match="invalid literal for int"):
        opt.set("not-an-int")


def test_immutable_option():
    opt = Option("A_FAKE_OPTION", "default-value", immutable=True)
    with pytest.raises(TypeError, match="cannot be modified after initial load"):
        opt.set("a-new-value")


def test_option_reset():
    opt = Option("A_FAKE_OPTION", "default-value")
    opt.set("a-new-value")
    assert opt.get() == "a-new-value"
    opt.reset()
    assert opt.get() == "default-value"


def test_option_set_returns_last_value():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert opt.set("a-new-value") == "default-value"
