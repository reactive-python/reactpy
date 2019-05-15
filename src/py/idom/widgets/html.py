from .common import node_constructor

__all__ = [
    # Content sectioning
    "style",
    "address",
    "article",
    "aside",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hgroup",
    "nav",
    "section",
    # Text content
    "blockquote",
    "blockquote",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "ul",
    # Inline text semantics
    "a",
    "abbr",
    "b",
    "br",
    "cite",
    "code",
    "data",
    "em",
    "i",
    "kbd",
    "mark",
    "q",
    "s",
    "samp",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "time",
    "u",
    "var",
    # Image and video
    "img",
    "audio",
    "video",
    "source",
    # Table content
    "caption",
    "col",
    "colgroup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    # Forms
    "meter",
    "output",
    "progress",
    "input",
    "button",
    "label",
    "fieldset",
    "legend",
    # Interactive elements
    "details",
    "dialog",
    "menu",
    "menuitem",
    "summary",
]

# Content sectioning
style = node_constructor("style")
address = node_constructor("address")
article = node_constructor("article")
aside = node_constructor("aside")
footer = node_constructor("footer")
h1 = node_constructor("h1")
h2 = node_constructor("h2")
h3 = node_constructor("h3")
h4 = node_constructor("h4")
h5 = node_constructor("h5")
h6 = node_constructor("h6")
header = node_constructor("header")
hgroup = node_constructor("hgroup")
nav = node_constructor("nav")
section = node_constructor("section")

# Text content
blockquote = node_constructor("blockquote")
dd = node_constructor("dd")
div = node_constructor("div")
dl = node_constructor("dl")
dt = node_constructor("dt")
figcaption = node_constructor("figcaption")
figure = node_constructor("figure")
hr = node_constructor("hr", allow_children=False)
li = node_constructor("li")
ol = node_constructor("ol")
p = node_constructor("p")
pre = node_constructor("pre")
ul = node_constructor("ul")

# Inline text semantics
a = node_constructor("a")
abbr = node_constructor("abbr")
b = node_constructor("b")
br = node_constructor("br", allow_children=False)
cite = node_constructor("cite")
code = node_constructor("code")
data = node_constructor("data")
em = node_constructor("em")
i = node_constructor("i")
kbd = node_constructor("kbd")
mark = node_constructor("mark")
q = node_constructor("q")
s = node_constructor("s")
samp = node_constructor("samp")
small = node_constructor("small")
span = node_constructor("span")
strong = node_constructor("strong")
sub = node_constructor("sub")
sup = node_constructor("sup")
time = node_constructor("time")
u = node_constructor("u")
var = node_constructor("var")

# Image and video
img = node_constructor("img", allow_children=False)
audio = node_constructor("audio")
video = node_constructor("video")
source = node_constructor("source", allow_children=False)

# Table content
caption = node_constructor("caption")
col = node_constructor("col")
colgroup = node_constructor("colgroup")
table = node_constructor("table")
tbody = node_constructor("tbody")
td = node_constructor("td")
tfoot = node_constructor("tfoot")
th = node_constructor("th")
thead = node_constructor("thead")
tr = node_constructor("tr")

# Forms
meter = node_constructor("meter")
output = node_constructor("output")
progress = node_constructor("progress")
input = node_constructor("input", allow_children=False)
button = node_constructor("button")
label = node_constructor("label")
fieldset = node_constructor("fieldset")
legend = node_constructor("legend")

# Interactive elements
details = node_constructor("details")
dialog = node_constructor("dialog")
menu = node_constructor("menu")
menuitem = node_constructor("menuitem")
summary = node_constructor("summary")
