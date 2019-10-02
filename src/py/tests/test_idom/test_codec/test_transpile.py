import pytest

from idom import html
from idom.codec.transpile import transpile_html_templates


@pytest.mark.parametrize(
    "code, model, local",
    [
        ("<div/>", html("div"), {}),
        ("<div myAttr=3 />", html("div", {"myAttr": "3"}), {}),
        ("<div myAttr={1 + 2} />", html("div", {"myAttr": 3}), {}),
        ("<div myAttr={a} />", html("div", {"myAttr": 3}), {"a": 3}),
        ("<div>inner HTML</div>", html("div", ["inner HTML"]), {}),
        ("<div>{'inner' + ' ' + 'HTML'}</div>", html("div", ["inner HTML"]), {}),
        ("<div>{inner}</div>", html("div", ["inner HTML"]), {"inner": "inner HTML"}),
        ("<div><img/></div>", html("div", [html("img")]), {}),
        ("<div>{ html'<div/>' }</div>", html("div", [html("div")]), {}),
        (
            "<div>{'a'} b {'c'} d</div>",  # left boundary case
            html("div", ["a", " b ", "c", " d"]),
            {"some": "some"},
        ),
        (
            "<div>a {'b'} c {'d'}</div>",  # right boundary case
            html("div", ["a ", "b", " c ", "d"]),
            {"some": "some"},
        ),
    ],
)
def test_transpile_html_templates(code, model, local):
    to_transpile = "html" + repr(code)  # add template prefix indicator
    assert eval(transpile_html_templates(to_transpile), globals(), local) == model
