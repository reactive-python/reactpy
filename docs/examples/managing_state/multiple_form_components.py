from conditional_form_component import form

from reactpy import component, html


# start
@component
def item(status):
    return html.section(html.h4("Form", status, ":"), form(status))


@component
def app():
    statuses = ["empty", "typing", "submitting", "success", "error"]
    status_list = [item(status) for status in statuses]
    return html._(status_list)
