import pytest

from reactpy import config
from reactpy.executors import utils


def test_invalid_vdom_head():
    with pytest.raises(ValueError):
        utils.vdom_head_to_html({"tagName": "invalid"})


def test_process_settings():
    utils.process_settings({"async_rendering": False})
    assert config.REACTPY_ASYNC_RENDERING.current is False
    utils.process_settings({"async_rendering": True})
    assert config.REACTPY_ASYNC_RENDERING.current is True


def test_invalid_setting():
    with pytest.raises(ValueError, match='Unknown ReactPy setting "foobar".'):
        utils.process_settings({"foobar": True})
