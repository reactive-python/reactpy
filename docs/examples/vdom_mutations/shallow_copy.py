from reactpy import html

# start
# The tag constructors copy the top level, so the element's own attributes and
# children containers are separate objects from the ones you passed in.
style = {"color": "red"}
attributes = {"id": "card", "style": style}
children = ["hello"]

element = html.div(attributes, *children)

print(element["attributes"] is attributes)  # False -- a copy
print(element["children"] is children)  # False -- a fresh list

# But the copy is shallow: nested values are still the objects you handed over.
print(element["attributes"].get("style") is style)  # True

style["color"] = "blue"
print(element["attributes"].get("style"))  # {'color': 'blue'} -- changed after the fact
# end
