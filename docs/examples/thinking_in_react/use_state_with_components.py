from reactpy import html

filter_text = ""
in_stock_only = False
products = ()

def search_bar(**_kw):
    ...

def product_table(**_kw):
    ...

# start
html.div(
    search_bar(filter_text=filter_text, in_stock_only=in_stock_only),
    product_table(products=products, filter_text=filter_text, in_stock_only=in_stock_only),
)
