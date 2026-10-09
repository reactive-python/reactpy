from reactpy import html

# start
# Void elements reject children -- loudly, at the call site.
try:
    html.br("oops")
except TypeError as error:
    print(error)  # 'br' nodes cannot have children.

print(html.br())  # {'tagName': 'br'}

# script is stricter still: one string child, no handlers, an inferred key.
print(html.script("var answered = 42;"))
# {'tagName': 'script', 'children': ['var answered = 42;'],
#  'attributes': {'key': 'var answered = 42;'}}

print(html.script({"src": "/chart.js"}))
# {'tagName': 'script', 'attributes': {'src': '/chart.js', 'key': '/chart.js'}}

try:
    html.script({"onLoad": lambda event: None}, "var x = 1;")
except ValueError as error:
    print(error)  # 'script' elements do not support event handlers
# end
