from reactpy import component, html, use_debug_value, use_state

# start


def use_cart():
    """A custom hook: it holds the cart and reports what it holds."""
    items, set_items = use_state([])

    # Logged to the server as `use_cart's component(...) <message>` whenever the
    # message differs from the last one logged. A plain string here would be
    # built on every render; reading state makes it change only when it should.
    use_debug_value(f"{len(items)} item(s): {', '.join(items) or '-'}")

    async def add(event=None):
        set_items([*items, f"item {len(items) + 1}"])

    return items, add


@component
def shop():
    items, add = use_cart()
    return html.div(
        html.h1(f"Cart ({len(items)})"),
        html.ul([html.li({"key": i}, item) for i, item in enumerate(items)]),
        html.button({"onClick": add}, "Add item"),
    )
