from reactpy import component, html

# start
# This alert fires when the component renders, not when clicked!
html.button({"on_click": lambda event: print('You clicked on me!')})