import os
from unittest import mock

import pytest

from reactpy._option import DeprecatedOption, Option


def test_option_repr():
    opt = Option("A_FAKE_OPTION", "some-value")
    assert opt.name == "A_FAKE_OPTION"
    assert repr(opt) == "Option(A_FAKE_OPTION='some-value')"


@mock.patch.dict(os.environ, {"A_FAKE_OPTION": "value-from-environ"})
def test_option_from_os_environ():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert opt.current == "value-from-environ"


def test_option_from_default():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert opt.current == "default-value"
    assert opt.current is opt.default


@mock.patch.dict(os.environ, {"A_FAKE_OPTION": "1"})
def test_option_validator():
    opt = Option("A_FAKE_OPTION", False, validator=lambda x: bool(int(x)))

    assert opt.current is True

    opt.current = "0"
    assert opt.current is False

    with pytest.raises(ValueError, match="invalid literal for int"):
        opt.current = "not-an-int"


def test_immutable_option():
    opt = Option("A_FAKE_OPTION", "default-value", mutable=False)
    assert not opt.mutable
    with pytest.raises(TypeError, match="cannot be modified after initial load"):
        opt.current = "a-new-value"
    with pytest.raises(TypeError, match="cannot be modified after initial load"):
        opt.unset()


def test_option_reset():
    opt = Option("A_FAKE_OPTION", "default-value")
    opt.current = "a-new-value"
    opt.unset()
    assert opt.current is opt.default
    assert not opt.is_set()


@mock.patch.dict(os.environ, {"A_FAKE_OPTION": "value-from-environ"})
def test_option_reload():
    opt = Option("A_FAKE_OPTION", "default-value")
    opt.current = "some-other-value"
    opt.reload()
    assert opt.current == "value-from-environ"


def test_option_set():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert not opt.is_set()
    opt.current = "a-new-value"
    assert opt.is_set()


def test_option_set_default():
    opt = Option("A_FAKE_OPTION", "default-value")
    assert not opt.is_set()
    assert opt.set_default("new-value") == "new-value"
    assert opt.is_set()


def test_cannot_subscribe_immutable_option():
    opt = Option("A_FAKE_OPTION", "default", mutable=False)
    with pytest.raises(TypeError, match="Immutable options cannot be subscribed to"):
        opt.subscribe(lambda value: None)


def test_option_subscribe():
    opt = Option("A_FAKE_OPTION", "default")

    calls = []
    opt.subscribe(calls.append)
    assert calls == ["default"]

    opt.current = "default"
    # value did not change, so no trigger
    assert calls == ["default"]

    opt.current = "new-1"
    opt.current = "new-2"
    assert calls == ["default", "new-1", "new-2"]

    opt.unset()
    assert calls == ["default", "new-1", "new-2", "default"]


def test_deprecated_option():
    opt = DeprecatedOption("is deprecated!", "A_FAKE_OPTION", None)

    with pytest.warns(DeprecationWarning, match="is deprecated!"):
        assert opt.current is None

    with pytest.warns(DeprecationWarning, match="is deprecated!"):
        opt.current = "something"
