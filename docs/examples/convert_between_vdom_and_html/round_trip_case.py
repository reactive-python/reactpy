from reactpy import html, reactpy_to_string, string_to_reactpy

# start
# HTML in, ReactPy out: camelCase comes back.
print(string_to_reactpy('<label for="email">Email</label>'))
# {'attributes': {'htmlFor': 'email'}, 'children': ['Email'], 'tagName': 'label'}

# ReactPy out: every attribute name is lowercased on the way out.
print(reactpy_to_string(html.label({"htmlFor": "email"}, "Email")))
# <label htmlfor="email">Email</label>

print(reactpy_to_string(html.label({"for": "email"}, "Email")))
# <label for="email">Email</label>

print(reactpy_to_string(html.div({"className": "card"}, "x")))
# <div classname="card">x</div>
# end
