from reactpy import component, html


def admin_panel():
    return []


def login_form():
    return []


is_logged_in = True


# start
@component
def my_component():
    if is_logged_in:
        content = admin_panel()
    else:
        content = login_form()
    return html.div(content)
