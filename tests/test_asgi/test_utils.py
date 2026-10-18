import pytest

from reactpy import config, html
from reactpy.executors import utils


def test_invalid_vdom_head():
    with pytest.raises(ValueError):
        utils.vdom_head_to_html({"tagName": "invalid"})


def test_prepend_body_content_as_vdom_dict():
    from reactpy.utils import reactpy_to_string

    assert (
        reactpy_to_string(
            html.div(html.p({"id": "noscript-message"}, "Please enable JavaScript."))
        )
        == '<div><p id="noscript-message">Please enable JavaScript.</p></div>'
    )


def test_prepend_body_content_as_noscript():
    from reactpy.utils import reactpy_to_string

    assert (
        reactpy_to_string(html.noscript(html.p("Enable JavaScript to view this site.")))
        == "<noscript><p>Enable JavaScript to view this site.</p></noscript>"
    )


def test_process_settings():
    utils.process_settings({"async_rendering": False})
    assert config.REACTPY_ASYNC_RENDERING.current is False
    utils.process_settings({"async_rendering": True})
    assert config.REACTPY_ASYNC_RENDERING.current is True
    utils.process_settings({"max_queue_size": 10})
    assert config.REACTPY_MAX_QUEUE_SIZE.current == 10


def test_invalid_setting():
    with pytest.raises(ValueError, match=r'Unknown ReactPy setting "foobar".'):
        utils.process_settings({"foobar": True})
