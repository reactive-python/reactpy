from data import people

from reactpy import component, html

# start


@component
def people_list():
    list_items = [
        html(
            {"key": person["id"]},
            html.h1(person["name"]),
            html.p(person["profession"]),
        )
        for person in people
    ]
    return html.div(list_items)
