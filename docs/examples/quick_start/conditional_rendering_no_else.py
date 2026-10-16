from reactpy import component, html


def admin_panel():
    return html.div("Admin")


is_logged_in = True


# start
@component
def my_component():
    # No `else` branch needed: unpack a one-item list, or an empty one.
    # Unpack the *component*, never the dict it returns -- `*admin_panel()`
    # would iterate the dict and emit its keys as text.
    # `is_logged_in and admin_panel()` would render the word "False".
    return html.div(*([admin_panel()] if is_logged_in else []))
