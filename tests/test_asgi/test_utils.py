from pathlib import Path

import pytest

import reactpy
from reactpy import config, html
from reactpy.executors import utils
from reactpy.types import VdomDict


def test_invalid_vdom_head():
    with pytest.raises(ValueError):
        utils.vdom_head_to_html({"tagName": "invalid"})


def test_html_noscript_path_to_html(tmp_path: Path):
    noscript_file = tmp_path / "noscript.html"
    noscript_file.write_text("<p>Please enable JavaScript.</p>", encoding="utf-8")

    assert (
        utils.html_noscript_to_html(noscript_file)
        == "<noscript><p>Please enable JavaScript.</p></noscript>"
    )



def test_html_noscript_string_to_html():
    assert (
        utils.html_noscript_to_html("<p>Please enable JavaScript.</p>")
        == "<noscript><p>Please enable JavaScript.</p></noscript>"
    )


def test_html_noscript_as_uncalled_component():
    @reactpy.component
    def message():
        return html.p({"id": "noscript-message"}, "Please enable JavaScript.")

    assert (
        utils.html_noscript_to_html(message)
        == '<noscript><p id="noscript-message">Please enable JavaScript.</p></noscript>'
    )


def test_html_noscript_as_function():
    def message():
        return html.p({"id": "noscript-message"}, "Please enable JavaScript.")

    assert (
        utils.html_noscript_to_html(message())
        == '<noscript><p id="noscript-message">Please enable JavaScript.</p></noscript>'
    )


def test_html_noscript_as_vdom_dict():
    assert (
        utils.html_noscript_to_html(VdomDict(tagName="div", children=[html.p({"id": "noscript-message"}, "Please enable JavaScript.")] ))
        == '<noscript><div><p id="noscript-message">Please enable JavaScript.</p></div></noscript>'
    )


def test_html_noscript_none_to_html():
    assert utils.html_noscript_to_html(None) == ""


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
