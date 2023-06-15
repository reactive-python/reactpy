from reactpy import component, html


def admin_panel():
    return []


def login_form():
    return []


is_logged_in = True


# start
@component
def my_component():
    return html.div(admin_panel() if is_logged_in else login_form())
