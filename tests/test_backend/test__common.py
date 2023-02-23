import pytest

from reactpy import html
from reactpy.backend._common import (
    CommonOptions,
    traversal_safe_path,
    vdom_head_elements_to_html,
)


def test_common_options_url_prefix_starts_with_slash():
    # no prefix specified
    CommonOptions(url_prefix="")

    with pytest.raises(ValueError, match="start with '/'"):
        CommonOptions(url_prefix="not-start-withslash")


@pytest.mark.parametrize(
    "bad_path",
    [
        "../escaped",
        "ok/../../escaped",
        "ok/ok-again/../../ok-yet-again/../../../escaped",
    ],
)
def test_catch_unsafe_relative_path_traversal(tmp_path, bad_path):
    with pytest.raises(ValueError, match="Unsafe path"):
        traversal_safe_path(tmp_path, *bad_path.split("/"))


@pytest.mark.parametrize(
    "vdom_in, html_out",
    [
        (
            "<title>example</title>",
            "<title>example</title>",
        ),
        (
            # We do not modify strings given by user. If given as VDOM we would have
            # striped this head element, but since provided as string, we leav as-is.
            "<head></head>",
            "<head></head>",
        ),
        (
            html.head(
                html.meta({"charset": "utf-8"}),
                html.title("example"),
            ),
            # we strip the head element
            '<meta charset="utf-8"><title>example</title>',
        ),
        (
            html._(
                html.meta({"charset": "utf-8"}),
                html.title("example"),
            ),
            '<meta charset="utf-8"><title>example</title>',
        ),
        (
            [
                html.meta({"charset": "utf-8"}),
                html.title("example"),
            ],
            '<meta charset="utf-8"><title>example</title>',
        ),
    ],
)
def test_vdom_head_elements_to_html(vdom_in, html_out):
    assert vdom_head_elements_to_html(vdom_in) == html_out
