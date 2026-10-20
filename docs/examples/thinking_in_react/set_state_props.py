from reactpy import component, hooks, html


def search_bar(**_kws): ...


# start
@component
def filterable_product_table(products):
    filter_text, set_filter_text = hooks.use_state("")
    in_stock_only, set_in_stock_only = hooks.use_state(False)

    return html.div(
        search_bar(
            filter_text=filter_text,
            in_stock_only=in_stock_only,
            set_filter_text=set_filter_text,
            set_in_stock_only=set_in_stock_only,
        )
    )
