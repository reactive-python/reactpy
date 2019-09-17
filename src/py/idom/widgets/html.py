from idom.core.vdom import make_vdom_constructor

__all__ = [
    # External sources
    "link",
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

# External sources
link = make_vdom_constructor("link", allow_children=False)

# Content sectioning
style = make_vdom_constructor("style")
address = make_vdom_constructor("address")
article = make_vdom_constructor("article")
aside = make_vdom_constructor("aside")
footer = make_vdom_constructor("footer")
h1 = make_vdom_constructor("h1")
h2 = make_vdom_constructor("h2")
h3 = make_vdom_constructor("h3")
h4 = make_vdom_constructor("h4")
h5 = make_vdom_constructor("h5")
h6 = make_vdom_constructor("h6")
header = make_vdom_constructor("header")
hgroup = make_vdom_constructor("hgroup")
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
br = make_vdom_constructor("br", allow_children=False)
cite = make_vdom_constructor("cite")
code = make_vdom_constructor("code")
data = make_vdom_constructor("data")
em = make_vdom_constructor("em")
i = make_vdom_constructor("i")
kbd = make_vdom_constructor("kbd")
mark = make_vdom_constructor("mark")
q = make_vdom_constructor("q")
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

# Image and video
img = make_vdom_constructor("img", allow_children=False)
audio = make_vdom_constructor("audio")
video = make_vdom_constructor("video")
source = make_vdom_constructor("source", allow_children=False)

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
meter = make_vdom_constructor("meter")
output = make_vdom_constructor("output")
progress = make_vdom_constructor("progress")
input = make_vdom_constructor("input", allow_children=False)
button = make_vdom_constructor("button")
label = make_vdom_constructor("label")
fieldset = make_vdom_constructor("fieldset")
legend = make_vdom_constructor("legend")

# Interactive elements
details = make_vdom_constructor("details")
dialog = make_vdom_constructor("dialog")
menu = make_vdom_constructor("menu")
menuitem = make_vdom_constructor("menuitem")
summary = make_vdom_constructor("summary")
