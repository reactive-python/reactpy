"""
**Fragment**

- :func:`_`

**Dcument metadata**

- :func:`base`
- :func:`head`
- :func:`link`
- :func:`meta`
- :func:`style`
- :func:`title`

**Content sectioning**

- :func:`address`
- :func:`article`
- :func:`aside`
- :func:`footer`
- :func:`header`
- :func:`h1`
- :func:`h2`
- :func:`h3`
- :func:`h4`
- :func:`h5`
- :func:`h6`
- :func:`main`
- :func:`nav`
- :func:`section`

**Text content**

- :func:`blockquote`
- :func:`dd`
- :func:`div`
- :func:`dl`
- :func:`dt`
- :func:`figcaption`
- :func:`figure`
- :func:`hr`
- :func:`li`
- :func:`ol`
- :func:`p`
- :func:`pre`
- :func:`ul`

**Inline text semantics**

- :func:`a`
- :func:`abbr`
- :func:`b`
- :func:`bdi`
- :func:`bdo`
- :func:`br`
- :func:`cite`
- :func:`code`
- :func:`data`
- :func:`em`
- :func:`i`
- :func:`kbd`
- :func:`mark`
- :func:`q`
- :func:`rp`
- :func:`rt`
- :func:`ruby`
- :func:`s`
- :func:`samp`
- :func:`small`
- :func:`span`
- :func:`strong`
- :func:`sub`
- :func:`sup`
- :func:`time`
- :func:`u`
- :func:`var`
- :func:`wbr`

**Image and video**

- :func:`area`
- :func:`audio`
- :func:`img`
- :func:`map`
- :func:`track`
- :func:`video`

**Embedded content**

- :func:`embed`
- :func:`iframe`
- :func:`object`
- :func:`param`
- :func:`picture`
- :func:`portal`
- :func:`source`

**SVG and MathML**

- :func:`svg`
- :func:`math`

**Scripting**

- :func:`canvas`
- :func:`noscript`
- :func:`script`

**Demarcating edits**

- :func:`del_`
- :func:`ins`

**Table content**

- :func:`caption`
- :func:`col`
- :func:`colgroup`
- :func:`table`
- :func:`tbody`
- :func:`td`
- :func:`tfoot`
- :func:`th`
- :func:`thead`
- :func:`tr`

**Forms**

- :func:`button`
- :func:`fieldset`
- :func:`form`
- :func:`input`
- :func:`label`
- :func:`legend`
- :func:`meter`
- :func:`option`
- :func:`output`
- :func:`progress`
- :func:`select`
- :func:`textarea`

**Interactive elements**

- :func:`details`
- :func:`dialog`
- :func:`menu`
- :func:`menuitem`
- :func:`summary`

**Web components**

- :func:`slot`
- :func:`template`

.. autofunction:: _
"""

from __future__ import annotations

from typing import Any, Mapping

from idom.core.types import Key, VdomDict
from idom.core.vdom import coalesce_attributes_and_children, make_vdom_constructor


__all__ = (
    "_",
    "a",
    "abbr",
    "address",
    "area",
    "article",
    "aside",
    "audio",
    "b",
    "base",
    "bdi",
    "bdo",
    "blockquote",
    "br",
    "button",
    "canvas",
    "caption",
    "cite",
    "code",
    "col",
    "colgroup",
    "data",
    "dd",
    "del_",
    "details",
    "dialog",
    "div",
    "dl",
    "dt",
    "em",
    "embed",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hr",
    "i",
    "iframe",
    "img",
    "input",
    "ins",
    "kbd",
    "label",
    "legend",
    "li",
    "link",
    "main",
    "map",
    "mark",
    "math",
    "menu",
    "menuitem",
    "meta",
    "meter",
    "nav",
    "noscript",
    "object",
    "ol",
    "option",
    "output",
    "p",
    "param",
    "picture",
    "portal",
    "pre",
    "progress",
    "q",
    "rp",
    "rt",
    "ruby",
    "s",
    "samp",
    "script",
    "section",
    "select",
    "slot",
    "small",
    "source",
    "span",
    "strong",
    "style",
    "sub",
    "summary",
    "sup",
    "svg",
    "table",
    "tbody",
    "td",
    "template",
    "textarea",
    "tfoot",
    "th",
    "thead",
    "time",
    "title",
    "tr",
    "track",
    "u",
    "ul",
    "var",
    "video",
    "wbr",
)


def _(*children: Any, key: Key | None = None) -> VdomDict:
    """An HTML fragment - this element will not appear in the DOM"""
    attributes, coalesced_children = coalesce_attributes_and_children(children)
    if attributes:
        raise TypeError("Fragments cannot have attributes")
    model: VdomDict = {"tagName": ""}

    if coalesced_children:
        model["children"] = coalesced_children

    if key is not None:
        model["key"] = key

    return model


# Dcument metadata
base = make_vdom_constructor("base")
head = make_vdom_constructor("head")
link = make_vdom_constructor("link")
meta = make_vdom_constructor("meta")
style = make_vdom_constructor("style")
title = make_vdom_constructor("title")

# Content sectioning
address = make_vdom_constructor("address")
article = make_vdom_constructor("article")
aside = make_vdom_constructor("aside")
footer = make_vdom_constructor("footer")
header = make_vdom_constructor("header")
h1 = make_vdom_constructor("h1")
h2 = make_vdom_constructor("h2")
h3 = make_vdom_constructor("h3")
h4 = make_vdom_constructor("h4")
h5 = make_vdom_constructor("h5")
h6 = make_vdom_constructor("h6")
main = make_vdom_constructor("main")
nav = make_vdom_constructor("nav")
section = make_vdom_constructor("section")

# Text content
blockquote = make_vdom_constructor("blockquote")
dd = make_vdom_constructor("dd")
div = make_vdom_constructor("div")
dl = make_vdom_constructor("dl")
dt = make_vdom_constructor("dt")
figcaption = make_vdom_constructor("figcaption")
figure = make_vdom_constructor("figure")
hr = make_vdom_constructor("hr", allow_children=False)
li = make_vdom_constructor("li")
ol = make_vdom_constructor("ol")
p = make_vdom_constructor("p")
pre = make_vdom_constructor("pre")
ul = make_vdom_constructor("ul")

# Inline text semantics
a = make_vdom_constructor("a")
abbr = make_vdom_constructor("abbr")
b = make_vdom_constructor("b")
bdi = make_vdom_constructor("bdi")
bdo = make_vdom_constructor("bdo")
br = make_vdom_constructor("br", allow_children=False)
cite = make_vdom_constructor("cite")
code = make_vdom_constructor("code")
data = make_vdom_constructor("data")
em = make_vdom_constructor("em")
i = make_vdom_constructor("i")
kbd = make_vdom_constructor("kbd")
mark = make_vdom_constructor("mark")
q = make_vdom_constructor("q")
rp = make_vdom_constructor("rp")
rt = make_vdom_constructor("rt")
ruby = make_vdom_constructor("ruby")
s = make_vdom_constructor("s")
samp = make_vdom_constructor("samp")
small = make_vdom_constructor("small")
span = make_vdom_constructor("span")
strong = make_vdom_constructor("strong")
sub = make_vdom_constructor("sub")
sup = make_vdom_constructor("sup")
time = make_vdom_constructor("time")
u = make_vdom_constructor("u")
var = make_vdom_constructor("var")
wbr = make_vdom_constructor("wbr")

# Image and video
area = make_vdom_constructor("area", allow_children=False)
audio = make_vdom_constructor("audio")
img = make_vdom_constructor("img", allow_children=False)
map = make_vdom_constructor("map")
track = make_vdom_constructor("track")
video = make_vdom_constructor("video")

# Embedded content
embed = make_vdom_constructor("embed", allow_children=False)
iframe = make_vdom_constructor("iframe", allow_children=False)
object = make_vdom_constructor("object")
param = make_vdom_constructor("param")
picture = make_vdom_constructor("picture")
portal = make_vdom_constructor("portal", allow_children=False)
source = make_vdom_constructor("source", allow_children=False)

# SVG and MathML
svg = make_vdom_constructor("svg")
math = make_vdom_constructor("math")

# Scripting
canvas = make_vdom_constructor("canvas")
noscript = make_vdom_constructor("noscript")


def script(
    *attributes_and_children: Mapping[str, Any] | str,
    key: str | int | None = None,
) -> VdomDict:
    """Create a new `<{script}> <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script>`__ element.

    This behaves slightly differently than a normal script element in that it may be run
    multiple times if its key changes (depending on specific browser behaviors). If no
    key is given, the key is inferred to be the content of the script or, lastly its
    'src' attribute if that is given.

    If no attributes are given, the content of the script may evaluate to a function.
    This function will be called when the script is initially created or when the
    content of the script changes. The function may itself optionally return a teardown
    function that is called when the script element is removed from the tree, or when
    the script content changes.
    """
    model: VdomDict = {"tagName": "script"}

    attributes, children = coalesce_attributes_and_children(attributes_and_children)

    if children:
        if len(children) > 1:
            raise ValueError("'script' nodes may have, at most, one child.")
        elif not isinstance(children[0], str):
            raise ValueError("The child of a 'script' must be a string.")
        else:
            model["children"] = children
            if key is None:
                key = children[0]

    if attributes:
        model["attributes"] = attributes
        if key is None and not children and "src" in attributes:
            key = attributes["src"]

    if key is not None:
        model["key"] = key

    return model


# Demarcating edits
del_ = make_vdom_constructor("del")
ins = make_vdom_constructor("ins")

# Table content
caption = make_vdom_constructor("caption")
col = make_vdom_constructor("col")
colgroup = make_vdom_constructor("colgroup")
table = make_vdom_constructor("table")
tbody = make_vdom_constructor("tbody")
td = make_vdom_constructor("td")
tfoot = make_vdom_constructor("tfoot")
th = make_vdom_constructor("th")
thead = make_vdom_constructor("thead")
tr = make_vdom_constructor("tr")

# Forms
button = make_vdom_constructor("button")
fieldset = make_vdom_constructor("fieldset")
form = make_vdom_constructor("form")
input = make_vdom_constructor("input", allow_children=False)
label = make_vdom_constructor("label")
legend = make_vdom_constructor("legend")
meter = make_vdom_constructor("meter")
option = make_vdom_constructor("option")
output = make_vdom_constructor("output")
progress = make_vdom_constructor("progress")
select = make_vdom_constructor("select")
textarea = make_vdom_constructor("textarea")

# Interactive elements
details = make_vdom_constructor("details")
dialog = make_vdom_constructor("dialog")
menu = make_vdom_constructor("menu")
menuitem = make_vdom_constructor("menuitem")
summary = make_vdom_constructor("summary")

# Web components
slot = make_vdom_constructor("slot")
template = make_vdom_constructor("template")
