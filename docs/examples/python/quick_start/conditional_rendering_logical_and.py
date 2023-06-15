from reactpy import component, html


def admin_panel():
    return []


is_logged_in = True


# start
@component
def my_component():
    return html.div(is_logged_in and admin_panel())
