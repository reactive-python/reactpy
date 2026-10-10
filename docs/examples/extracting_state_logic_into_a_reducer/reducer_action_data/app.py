"""The fix: a module-level reducer that reads everything from the action."""

from reactpy import component, html, use_reducer, use_state

# start
INITIAL = {"count": 0, "total": 0}


def cart_reducer(state, action):
    """Pure and self-contained: every value it needs arrives in the action."""
    if action["type"] == "add":
        return {
            "count": state["count"] + 1,
            "total": state["total"] + action["price"],
        }
    return state


@component
def cart(item_price):
    # Defined at module level, so there is no enclosing scope to freeze.
    state, dispatch = use_reducer(cart_reducer, INITIAL)

    def handle_add(event):
        # The handler closes over the *current* price, and hands it over.
        dispatch({"type": "add", "price": item_price})

    return html.div(
        html.button({"onClick": handle_add}, "Add"),
        html.p(
            {"id": "cart"},
            f"count={state['count']} total={state['total']} price={item_price}",
        ),
    )


@component
def price_control():
    price, set_price = use_state(10)

    def raise_price(event):
        set_price(50)

    return html.div(
        html.button({"onClick": raise_price}, "Raise price"),
        cart(price),
        html.p(f"parent price={price}"),
    )


@component
def app():
    return price_control()
