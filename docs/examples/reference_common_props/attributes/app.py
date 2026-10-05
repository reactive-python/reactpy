from reactpy import component, html

# start

ROWS = [
    {"id": 1, "name": "Dana", "role": "admin", "active": True},
    {"id": 2, "name": "Sam", "role": "viewer", "active": False},
]


@component
def row(person):
    # `key` lives in attributes, `data-*` and `aria-*` are forwarded verbatim,
    # and `class` works exactly like `className`. Style values carry their own
    # units, because a bare number is not portable across executors.
    return html.tr(
        {
            "key": person["id"],
            "class": "is-active" if person["active"] else "is-inactive",
            "data-role": person["role"],
            "aria-label": f"{person['name']}, {person['role']}",
            "style": {"opacity": "1" if person["active"] else "0.55"},
        },
        html.td(person["name"]),
        html.td(person["role"]),
        html.td(
            {"style": {"text-align": "right", "font-variant-numeric": "tabular-nums"}},
            "yes" if person["active"] else "no",
        ),
    )


@component
def people_table():
    return html.table(
        None,
        html.thead(
            html.tr(
                None,
                html.th("Name"),
                html.th("Role"),
                html.th({"scope": "col"}, "Active"),
            )
        ),
        # A list of children: every row needs a key or state will follow the
        # row's position rather than the person.
        html.tbody(None, [row(person) for person in ROWS]),
    )
