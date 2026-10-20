from reactpy import string_to_reactpy

# start
model = string_to_reactpy('<div class="card"><h1>My Todo List</h1></div>')

print(model["tagName"])  # div
print(model["attributes"])  # {'className': 'card'}
print(model["children"])  # [{'tagName': 'h1', 'children': ['My Todo List']}]

# Nested children are full models too, which is easiest to see with pprint:
# pprint(model, sort_dicts=False)
# {'children': [{'children': ['My Todo List'], 'tagName': 'h1'}],
#  'attributes': {'className': 'card'},
#  'tagName': 'div'}
# end

# Indented input keeps the whitespace between tags as text children.
spaced = string_to_reactpy("<ul>\n  <li>a</li>\n  <li>b</li>\n</ul>")
print(spaced["children"])  # [{...}, '\n  ', {...}, '\n']

# A handler written as a string in the HTML becomes client-side JavaScript.
print(string_to_reactpy('<button onClick="this.innerText = 1">x</button>'))
# {'children': ['x'], 'inlineJavaScript': {'onClick': 'this.innerText = 1'},
#  'tagName': 'button'}
