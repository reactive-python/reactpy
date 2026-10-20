from reactpy import component, reactpy_to_string, string_to_reactpy


# start
@component
def card():
    return string_to_reactpy('<div class="card"><b>rendered from a string</b></div>')


print(reactpy_to_string(card()))
# <div class="card"><b>rendered from a string</b></div>
# end
