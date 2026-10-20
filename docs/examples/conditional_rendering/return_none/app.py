from reactpy import component, html


# start
@component
def item(name, is_packed):
    if is_packed:
        return None
    return html.li({"className": "item"}, name)


@component
def packing_list():
    return html.section(
        html.h1("Sally Ride's Packing List"),
        html.ul(
            item(is_packed=False, name="Space suit"),
            item(is_packed=False, name="Helmet with a golden leaf"),
            item(is_packed=True, name="Photo of Tam"),
        ),
    )
