from data import friends, get_image_url

from reactpy import component, html


# start
@component
def cat_friends():
    return html(
        html.div(
            {"id": "carousel", "className": "carousel"},
            [
                html.li(
                    {"key": person["id"], "id": f"friend-{person['id']}"},
                    html.img({"src": get_image_url(person), "alt": person["name"]}),
                )
                for person in friends
            ],
        ),
        html.div(
            {"className": "buttons"},
            [
                html.button(
                    {
                        "key": person["id"],
                        "onClick": f"document.getElementById('friend-{person['id']}')"
                        ".scrollIntoView({behavior: 'smooth', inline: 'center'})",
                    },
                    person["name"].split()[0],
                )
                for person in friends
            ],
        ),
    )
