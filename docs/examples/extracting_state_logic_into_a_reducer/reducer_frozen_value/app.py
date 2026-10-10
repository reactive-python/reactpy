"""A reducer closes over a value from the component body — and keeps the first one."""

from reactpy import component, html, use_reducer, use_state

# start
INITIAL = {"count": 0, "total": 0}


@component
def cart(item_price):
    # This reducer reads item_price from the enclosing scope. ReactPy keeps the
    # reducer from the first render, so it keeps the first price too.
    def reducer(state, action):
        if action["type"] == "add":
            return {
                "count": state["count"] + 1,
                "total": state["total"] + item_price,
            }
        return state

    state, dispatch = use_reducer(reducer, INITIAL)

    def handle_add(event):
        dispatch({"type": "add"})

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
