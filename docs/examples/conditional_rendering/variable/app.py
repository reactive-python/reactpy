from reactpy import component, html


# start
@component
def item(name, is_packed):
    item_content = name
    if is_packed:
        item_content = html.del_(f"{name} ✔")
    return html.li({"className": "item"}, item_content)


@component
def packing_list():
    return html.section(
        html.h1("Sally Ride's Packing List"),
        html.ul(
            item(is_packed=True, name="Space suit"),
            item(is_packed=True, name="Helmet with a golden leaf"),
            item(is_packed=False, name="Photo of Tam"),
        ),
    )
