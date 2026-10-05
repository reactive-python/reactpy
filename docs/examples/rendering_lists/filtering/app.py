from data import get_image_url, people

from reactpy import component, html

# start


@component
def people_list():
    chemists = [person for person in people if person["profession"] == "chemist"]
    list_items = [
        html.li(
            {"key": person["id"]},
            html.img({"src": get_image_url(person), "alt": person["name"]}),
            html.p(
                html.b(person["name"]),
                f" {person['profession']} known for {person['accomplishment']}",
            ),
        )
        for person in chemists
    ]
    return html.ul(list_items)
