from reactpy import html

# start
# The tag name is whatever you ask for -- there is no allow-list to consult.
print(html.div({"id": "greeting"}, "Hello"))
# {'tagName': 'div', 'attributes': {'id': 'greeting'}, 'children': ['Hello']}

print(html.definitely_not_a_real_tag("still renders"))
# {'tagName': 'definitely-not-a-real-tag', 'children': ['still renders']}
# end
