from reactpy import component, html


# start
@component
def search_bar(filter_text, in_stock_only):
    return html.form(
        html.input(
            {
                "type": "text",
                "value": filter_text,
                "placeholder": "Search...",
            }
        ),
        html.p(
            html.input({"type": "checkbox", "checked": in_stock_only}),
            "Only show products in stock",
        ),
    )
