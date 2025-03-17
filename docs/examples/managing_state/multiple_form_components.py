# start
from conditional_form_component import form

from reactpy import component, html


@component
def item(status):
    return html.section(html.h4("Form", status, ":"), form(status))


@component
def app():
    statuses = ["empty", "typing", "submitting", "success", "error"]
    return html.fragment([item(status) for status in statuses])
