"""A handler reads the values of the render that produced it. Click faster than
the server can re-render and every click sees the same snapshot — the safe
updater form is the fix.
"""

from reactpy import component, html, use_state


# start
@component
def basket():
    items, set_items = use_state([])
    discount, set_discount = use_state(0)

    async def add_naive(event):
        # reads `items` and `discount` from whichever render created this handler
        print(f"naive: {len(items)} items, discount={discount}")
        set_items([*items, f"item-{len(items) + 1}@{discount}"])

    async def add_safe(event):
        # the updater receives the *current* state at the moment it is applied
        def append(current):
            print(f"safe: {len(current)} items, discount={discount}")
            return [*current, f"item-{len(current) + 1}@{discount}"]

        set_items(append)

    async def handle_discount_click(e):
        set_discount(discount + 10)

    return html.div(
        html.button({"onClick": add_naive}, "Add (naive)"),
        html.button({"onClick": add_safe}, "Add (safe)"),
        html.button({"onClick": handle_discount_click}, f"Coupon {discount}%"),
        html.p(", ".join(items) or "empty basket"),
    )


@component
def app():
    return basket()
