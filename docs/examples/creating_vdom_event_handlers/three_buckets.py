from reactpy import html


# start
# ReactPy sorts each value in the attribute dict into one of three buckets
# by *kind*, not by name (core/vdom.py, separate_attributes_handlers_and_inline_javascript).
async def save(event):
    print("saved", await event.target.value)


element = html.button(
    {
        "id": "save",  # str, not onXxx -> attribute
        "onClick": save,  # callable -> event handler
        "onHover": "console.log('hover')",  # str under onXxx -> inline JS
        "data-row": "3",  # str, not onXxx -> attribute
    },
    "Save",
)

print(sorted(element))
# ['attributes', 'children', 'eventHandlers', 'inlineJavaScript', 'tagName']
print(sorted(element["attributes"]))  # ['data-row', 'id']
print(sorted(element["eventHandlers"]))  # ['onClick']
print(sorted(element["inlineJavaScript"]))  # ['onHover']
# end
