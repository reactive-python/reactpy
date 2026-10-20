from reactpy import component, html

# start
people = [
    "Creola Katherine Johnson: mathematician",
    "Mario José Molina-Pasquel Henríquez: chemist",
    "Mohammad Abdus Salam: physicist",
    "Percy Lavon Julian: chemist",
    "Subrahmanyan Chandrasekhar: astrophysicist",
]


@component
def people_list():
    list_items = [html.li(person) for person in people]
    return html.ul(list_items)
