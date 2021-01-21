from base64 import b64encode
from typing import Any, Dict, Union, Optional, Callable

import idom
from idom.core.vdom import (
    component,
    make_vdom_constructor,
    VdomDictConstructor,
    VdomDict,
)


def image(
    format: str,
    value: Union[str, bytes] = "",
    attributes: Optional[Dict[str, Any]] = None,
) -> VdomDict:
    """Utility for constructing an image from a string or bytes

    The source value will automatically be encoded to base64
    """
    if format == "svg":
        format = "svg+xml"

    if isinstance(value, str):
        bytes_value = value.encode()
    else:
        bytes_value = value

    base64_value = b64encode(bytes_value).decode()
    src = f"data:image/{format};base64,{base64_value}"

    return {"tagName": "img", "attributes": {"src": src, **(attributes or {})}}


@idom.component
def Input(
    callback: Callable[[str], None],
    type: str,
    value: str = "",
    attributes: Optional[Dict[str, Any]] = None,
    cast: Optional[Callable[[str], Any]] = None,
    ignore_empty: bool = True,
) -> VdomDict:
    """Utility for making an ``<input/>`` with a callback"""
    attrs = attributes or {}
    value, set_value = idom.hooks.use_state(value)

    events = idom.Events()

    @events.on("change")
    def on_change(event: Dict[str, Any]) -> None:
        value = event["value"]
        set_value(value)
        if not value and ignore_empty:
            return
        callback(value if cast is None else cast(value))

    return html.input({"type": type, "value": value, **attrs}, event_handlers=events)


class Html:
    """Utility for making basic HTML elements

    Many basic elements already have constructors, however accessing an attribute
    of any name on this object will return a constructor for an element with the
    same ``tagName``.

    All constructors return :class:`~idom.core.vdom.VdomDict`.
    """

    __call__ = staticmethod(component)

    def __init__(self) -> None:
        # External sources
        self.link = make_vdom_constructor("link", allow_children=False)

        # Content sectioning
        self.style = make_vdom_constructor("style")
        self.address = make_vdom_constructor("address")
        self.article = make_vdom_constructor("article")
        self.aside = make_vdom_constructor("aside")
        self.footer = make_vdom_constructor("footer")
        self.h1 = make_vdom_constructor("h1")
        self.h2 = make_vdom_constructor("h2")
        self.h3 = make_vdom_constructor("h3")
        self.h4 = make_vdom_constructor("h4")
        self.h5 = make_vdom_constructor("h5")
        self.h6 = make_vdom_constructor("h6")
        self.header = make_vdom_constructor("header")
        self.hgroup = make_vdom_constructor("hgroup")
        self.nav = make_vdom_constructor("nav")
        self.section = make_vdom_constructor("section")

        # Text content
        self.blockquote = make_vdom_constructor("blockquote")
        self.dd = make_vdom_constructor("dd")
        self.div = make_vdom_constructor("div")
        self.dl = make_vdom_constructor("dl")
        self.dt = make_vdom_constructor("dt")
        self.figcaption = make_vdom_constructor("figcaption")
        self.figure = make_vdom_constructor("figure")
        self.hr = make_vdom_constructor("hr", allow_children=False)
        self.li = make_vdom_constructor("li")
        self.ol = make_vdom_constructor("ol")
        self.p = make_vdom_constructor("p")
        self.pre = make_vdom_constructor("pre")
        self.ul = make_vdom_constructor("ul")

        # Inline text semantics
        self.a = make_vdom_constructor("a")
        self.abbr = make_vdom_constructor("abbr")
        self.b = make_vdom_constructor("b")
        self.br = make_vdom_constructor("br", allow_children=False)
        self.cite = make_vdom_constructor("cite")
        self.code = make_vdom_constructor("code")
        self.data = make_vdom_constructor("data")
        self.em = make_vdom_constructor("em")
        self.i = make_vdom_constructor("i")
        self.kbd = make_vdom_constructor("kbd")
        self.mark = make_vdom_constructor("mark")
        self.q = make_vdom_constructor("q")
        self.s = make_vdom_constructor("s")
        self.samp = make_vdom_constructor("samp")
        self.small = make_vdom_constructor("small")
        self.span = make_vdom_constructor("span")
        self.strong = make_vdom_constructor("strong")
        self.sub = make_vdom_constructor("sub")
        self.sup = make_vdom_constructor("sup")
        self.time = make_vdom_constructor("time")
        self.u = make_vdom_constructor("u")
        self.var = make_vdom_constructor("var")

        # Image and video
        self.img = make_vdom_constructor("img", allow_children=False)
        self.audio = make_vdom_constructor("audio")
        self.video = make_vdom_constructor("video")
        self.source = make_vdom_constructor("source", allow_children=False)

        # Table content
        self.caption = make_vdom_constructor("caption")
        self.col = make_vdom_constructor("col")
        self.colgroup = make_vdom_constructor("colgroup")
        self.table = make_vdom_constructor("table")
        self.tbody = make_vdom_constructor("tbody")
        self.td = make_vdom_constructor("td")
        self.tfoot = make_vdom_constructor("tfoot")
        self.th = make_vdom_constructor("th")
        self.thead = make_vdom_constructor("thead")
        self.tr = make_vdom_constructor("tr")

        # Forms
        self.meter = make_vdom_constructor("meter")
        self.output = make_vdom_constructor("output")
        self.progress = make_vdom_constructor("progress")
        self.input = make_vdom_constructor("input", allow_children=False)
        self.button = make_vdom_constructor("button")
        self.label = make_vdom_constructor("label")
        self.fieldset = make_vdom_constructor("fieldset")
        self.legend = make_vdom_constructor("legend")

        # Interactive elements
        self.details = make_vdom_constructor("details")
        self.dialog = make_vdom_constructor("dialog")
        self.menu = make_vdom_constructor("menu")
        self.menuitem = make_vdom_constructor("menuitem")
        self.summary = make_vdom_constructor("summary")

    def __getattr__(self, tag: str) -> VdomDictConstructor:
        return make_vdom_constructor(tag)


html = Html()
"""Holds pre-made constructors for basic HTML elements

See :class:`Html` for more info.
"""
