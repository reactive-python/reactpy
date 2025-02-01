import pytest

from reactpy import config
from reactpy.asgi import utils


def test_invalid_dotted_path():
    with pytest.raises(ValueError, match='"abc" is not a valid dotted path.'):
        utils.import_dotted_path("abc")


def test_invalid_component():
    with pytest.raises(
        AttributeError, match='ReactPy failed to import "foobar" from "reactpy"'
    ):
        utils.import_dotted_path("reactpy.foobar")


def test_invalid_module():
    with pytest.raises(ImportError, match='ReactPy failed to import "foo"'):
        utils.import_dotted_path("foo.bar")


def test_invalid_vdom_head():
    with pytest.raises(ValueError, match="Invalid head element!*"):
        utils.vdom_head_to_html({"tagName": "invalid"})


def test_process_settings():
    utils.process_settings({"async_rendering": False})
    assert config.REACTPY_ASYNC_RENDERING.current is False
    utils.process_settings({"async_rendering": True})
    assert config.REACTPY_ASYNC_RENDERING.current is True


def test_invalid_setting():
    with pytest.raises(ValueError, match='Unknown ReactPy setting "foobar".'):
        utils.process_settings({"foobar": True})
