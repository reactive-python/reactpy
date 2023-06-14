from reactpy import component, html


# start
@component
def my_button(count, on_click):
    return html.button({"on_click": on_click}, f"Clicked {count} times")
