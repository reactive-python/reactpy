from reactpy import component, html, use_state


# start
@component
def filterable_product_table(products):
    filter_text, set_filter_text = use_state("")
    in_stock_only, set_in_stock_only = use_state(False)

    return html.div(
        search_bar(filter_text=filter_text, in_stock_only=in_stock_only),
        product_table(
            products=products, filter_text=filter_text, in_stock_only=in_stock_only
        ),
    )


@component
def product_category_row(category):
    return html.tr(
        html.th({"colspan": 2}, category),
    )


@component
def product_row(product):
    if product["stocked"]:
        name = product["name"]
    else:
        name = html.span({"style": {"color": "red"}}, product["name"])

    return html.tr(
        html.td(name),
        html.td(product["price"]),
    )


@component
def product_table(products, filter_text, in_stock_only):
    rows = []
    last_category = None

    for product in products:
        if filter_text.lower() not in product["name"].lower():
            continue
        if in_stock_only and not product["stocked"]:
            continue
        if product["category"] != last_category:
            rows.append(
                product_category_row(product["category"], key=product["category"])
            )
        rows.append(product_row(product, key=product["name"]))
        last_category = product["category"]

    return html.table(
        html.thead(
            html.tr(
                html.th("Name"),
                html.th("Price"),
            ),
        ),
        html.tbody(rows),
    )


@component
def search_bar(filter_text, in_stock_only):
    return html.form(
        html.input({"type": "text", "value": filter_text, "placeholder": "Search..."}),
        html.label(
            html.input({"type": "checkbox", "checked": in_stock_only}),
            "Only show products in stock",
        ),
    )


PRODUCTS = [
    {"category": "Fruits", "price": "$1", "stocked": True, "name": "Apple"},
    {"category": "Fruits", "price": "$1", "stocked": True, "name": "Dragonfruit"},
    {"category": "Fruits", "price": "$2", "stocked": False, "name": "Passionfruit"},
    {"category": "Vegetables", "price": "$2", "stocked": True, "name": "Spinach"},
    {"category": "Vegetables", "price": "$4", "stocked": False, "name": "Pumpkin"},
    {"category": "Vegetables", "price": "$1", "stocked": True, "name": "Peas"},
]


@component
def app():
    return filterable_product_table(PRODUCTS)


# end
if __name__ == "__main__":
    from reactpy import run
    from reactpy.utils import _read_docs_css

    @component
    def styled_app():
        return html._(html.style(_read_docs_css()), app())

    run(styled_app)
