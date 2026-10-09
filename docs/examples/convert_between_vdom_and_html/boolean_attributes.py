from reactpy import html, reactpy_to_string

# start
# lxml knows a fixed list of boolean attributes. For those, the value is
# dropped and presence is all that survives -- False included.
print(reactpy_to_string(html.input({"type": "checkbox", "checked": False})))
# <input type="checkbox" checked>

# For everything else the value is str()-ed, so False leaks into the page.
print(reactpy_to_string(html.div({"hidden": False}, "still hidden")))
# <div hidden="False">still hidden</div>
# end
