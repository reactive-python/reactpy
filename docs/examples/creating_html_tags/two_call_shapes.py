from reactpy import html
from reactpy.types import VdomDict

# start
# Two call shapes: children only, or an attribute dict first.
print(html.button("Click Me"))
# {'tagName': 'button', 'children': ['Click Me']}

print(html.button({"id": "save", "disabled": True}, "Save"))
# {'tagName': 'button', 'attributes': {'id': 'save', 'disabled': True}, 'children': ['Save']}

# Only an *exact* dict counts as attributes -- a dict subclass is a child.
print(html.div(VdomDict(tagName="span")))
# {'tagName': 'div', 'children': [{'tagName': 'span'}]}
# end
