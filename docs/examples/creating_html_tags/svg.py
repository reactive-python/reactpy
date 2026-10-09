from reactpy import html

# start
# SVG lives on a second constructor, so html.svg.circle() does not collide
# with a hypothetical html.circle().
print(
    html.svg(
        {"width": "100", "height": "100", "viewBox": "0 0 100 100"},
        html.svg.circle({"cx": "50", "cy": "50", "r": "40", "fill": "tomato"}),
    )
)
# {'tagName': 'svg', 'attributes': {...},
#  'children': [{'tagName': 'circle', 'attributes': {...}}]}
# end

# Nested access needs the web-module constructor; plain html tags have no
# children to nest.
try:
    nested = "span"
    getattr(html.div, nested)("nope")
except AttributeError as error:
    print(error)  # Nested components can only be accessed on web module components.
