"""
Standard HTML Elements
======================


External sources
----------------

- :func:`link`


Content Sectioning
------------------

- :func:`style`
- :func:`address`
- :func:`article`
- :func:`aside`
- :func:`footer`
- :func:`h1`
- :func:`h2`
- :func:`h3`
- :func:`h4`
- :func:`h5`
- :func:`h6`
- :func:`header`
- :func:`hgroup`
- :func:`nav`
- :func:`section`


Text Content
------------
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


Inline Text Semantics
---------------------

- :func:`a`
- :func:`abbr`
- :func:`b`
- :func:`br`
- :func:`cite`
- :func:`code`
- :func:`data`
- :func:`em`
- :func:`i`
- :func:`kbd`
- :func:`mark`
- :func:`q`
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


Image and video
---------------

- :func:`img`
- :func:`audio`
- :func:`video`
- :func:`source`


Table Content
-------------

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


Forms
-----

- :func:`meter`
- :func:`output`
- :func:`progress`
- :func:`input`
- :func:`button`
- :func:`label`
- :func:`fieldset`
- :func:`legend`


Interactive Elements
--------------------

- :func:`details`
- :func:`dialog`
- :func:`menu`
- :func:`menuitem`
- :func:`summary`
"""

from .core.vdom import make_vdom_constructor


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
