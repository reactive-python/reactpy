from reactpy import html

from .rendering_lists_products import products

# start
list_items = [html.li({"key": product["id"]}, product["title"]) for product in products]
