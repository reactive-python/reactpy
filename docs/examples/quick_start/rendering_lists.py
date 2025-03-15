from reactpy import component, html

products = [
    {"title": "Cabbage", "is_fruit": False, "id": 1},
    {"title": "Garlic", "is_fruit": False, "id": 2},
    {"title": "Apple", "is_fruit": True, "id": 3},
]


@component
def shopping_list():
    list_items = [
        html.li(
            {
                "key": product["id"],
                "style": {"color": "magenta" if product["is_fruit"] else "darkgreen"},
            },
            product["title"],
        )
        for product in products
    ]

    return html.ul(list_items)
