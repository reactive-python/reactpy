from reactpy import html

# start
# Fragments carry no tag of their own: tagName is the empty string.
print(html.fragment(html.b("bold"), html.i("italic")))
# {'tagName': '', 'children': [{'tagName': 'b', ...}, {'tagName': 'i', ...}]}

# html(...) is html itself: HtmlConstructor.__call__ is the fragment call.
print(html(html.b("bold"))["tagName"])  # ''
print(html()["tagName"])  # '' -- an empty fragment

# A fragment may carry a key -- and nothing else.
print(html.fragment({"key": "row-1"}, html.b("x"))["attributes"])  # {'key': 'row-1'}

try:
    html.fragment({"className": "wrap"}, html.b("x"))
except TypeError as error:
    print(error)  # Fragments cannot have attributes besides 'key'
# end
