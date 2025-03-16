from reactpy import component, use_state


# start
@component
def filterable_product_table(products):
    filter_text, set_filter_text = use_state("")
    in_stock_only, set_in_stock_only = use_state(False)
