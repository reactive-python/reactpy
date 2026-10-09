from reactpy import html


# start
# Same behaviour, discovered by reading your bytecode instead of a decorator.
def submit(event):
    event.preventDefault()
    event.stopPropagation()
    event.debounce = 250


handler = html.form({"onSubmit": submit}, "x")["eventHandlers"]["onSubmit"]
print(handler.prevent_default)  # True
print(handler.stop_propagation)  # True
print(handler.debounce)  # 250
# end
